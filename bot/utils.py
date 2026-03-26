import html
import logging
import re
from datetime import datetime
from urllib.parse import urlparse

import httpx
from aiogram.types import BufferedInputFile, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_settings
from database.models import Event, EventRegistration, User, UserType
from database.session import SessionLocal

settings = get_settings()
PAGE_SIZE = 5


def _is_internal_media_host(netloc: str) -> bool:
    """Хост считается внутренним, если Telegram с интернета не достучится (localhost, api, minio и т.д.)."""
    if not netloc:
        return True
    host = netloc.split(":")[0].lower()
    if host in ("localhost", "127.0.0.1", "api", "backend", "app", "minio", "api-internal"):
        return True
    if "localhost" in host or host.startswith("127."):
        return True
    return False


def _media_url(url: str | None) -> str | None:
    """
    Возвращает URL медиа, доступный для Telegram (публичный).
    Логика как в content_plan_sender._ensure_public_media_url:
    - при заданном public_base: относительный путь → public_base + path;
    - абсолютный URL с внутренним хостом (localhost, api, minio…) → public_base + path.
    """
    if not url or not url.strip():
        return None
    u = url.strip()
    st = settings
    # Публичный base для медиа (как в API). S3 — без проверки use_s3, у бота нет ключей.
    public_base = None
    if getattr(st, "s3_public_base_url", None):
        public_base = (st.s3_public_base_url or "").rstrip("/")
    if not public_base and getattr(st, "upload_public_base_url", None):
        public_base = (st.upload_public_base_url or "").rstrip("/")
    if not public_base and getattr(st, "app_env", "").lower() == "prod":
        logging.warning(
            "Bot media: UPLOAD_PUBLIC_BASE_URL/S3_PUBLIC_BASE_URL not set in prod; media URLs may be unreachable by Telegram"
        )
    if public_base:
        if u.startswith(("http://", "https://")):
            if u.startswith(public_base):
                return u
            try:
                parsed = urlparse(u)
                if _is_internal_media_host(parsed.netloc or ""):
                    path = parsed.path or "/"
                    query = f"?{parsed.query}" if parsed.query else ""
                    return f"{public_base}{path}{query}"
            except Exception as e:
                logging.warning("Failed to rewrite media URL with public base: %s", e)
        else:
            # Относительный путь: /uploads/xxx или uploads/xxx → public_base + path
            path = u if u.startswith("/") else f"/{u}"
            return f"{public_base}{path}"
    if u.startswith(("http://", "https://")):
        return u
    base = (st.upload_base_url or "").rstrip("/")
    path = u if u.startswith("/") else f"/{u}"
    return f"{base}{path}" if base else None


def _is_video_url(url: str) -> bool:
    lower = url.lower()
    return any(lower.endswith(ext) for ext in (".mp4", ".webm", ".mov"))


def _is_image_url(url: str) -> bool:
    """Форматы, которые Telegram отображает как фото (answer_photo)."""
    lower = url.lower()
    return any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"))


def _media_kind(url: str, content_type: str = "") -> str:
    """'video' | 'photo' | 'document' — как отправлять файл."""
    if _is_video_url(url):
        return "video"
    if _is_image_url(url):
        return "photo"
    ct = content_type.lower()
    if ct.startswith("video/"):
        return "video"
    if ct.startswith("image/"):
        return "photo"
    return "document"


def _filename_from_url(url: str, default: str = "document.bin") -> str:
    """Имя файла из URL (последний сегмент пути) или default."""
    if not url:
        return default
    path = urlparse(url).path.strip("/")
    if path and "/" in path:
        return path.split("/")[-1] or default
    return path or default


def _fetch_url(raw_url: str | None) -> str | None:
    """URL, по которому бот может скачать файл (из своей сети: api, S3 и т.д.)."""
    if not raw_url or not raw_url.strip():
        return None
    u = raw_url.strip()
    if u.startswith(("http://", "https://")):
        return u
    base = (settings.upload_base_url or "").rstrip("/")
    path = u if u.startswith("/") else f"/{u}"
    return f"{base}{path}" if base else None


async def _fetch_media_bytes(url: str) -> tuple[bytes | None, str]:
    """Скачать медиа по URL. Возвращает (bytes, content_type) или (None, '')."""
    if not url:
        return None, ""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None, ""
            ct = (r.headers.get("content-type") or "").split(";")[0].strip() or "application/octet-stream"
            if "text/html" in ct:
                return None, ""
            return r.content, ct
    except Exception as e:
        logging.warning("Bot media fetch failed url=%s: %s", url[:80], e)
        return None, ""


def _description_for_telegram(html_desc: str | None) -> str:
    """Описание уже в HTML; нормализуем для Telegram. Telegram не поддерживает <br>, используем \\n."""
    if not html_desc or not html_desc.strip():
        return ""
    s = html_desc.strip()
    # Нормализуем неразрывные пробелы, чтобы в Telegram не отображалось как "&nbsp;".
    s = s.replace("\xa0", " ")
    s = re.sub(r"&#160;|&nbsp;", " ", s, flags=re.IGNORECASE)
    s = s.replace("</p>", "\n").replace("<p>", "")
    s = re.sub(r'\s+rel="[^"]*"', "", s)
    s = re.sub(r'\s+target="[^"]*"', "", s)
    s = re.sub(r'<br\s*/?>', "\n", s, flags=re.IGNORECASE)
    return s.strip()


async def _send_content_item(message: Message, item, parse_mode: str = "HTML") -> None:
    safe_title = html.escape(str(item.title))
    desc_html = _description_for_telegram(getattr(item, "description", None) or "")
    text = f"<b>{safe_title}</b>\n\n{desc_html}" if desc_html else f"<b>{safe_title}</b>"
    if len(text) > 4096:
        text = text[:4090] + "..."
    raw_url = getattr(item, "image_url", None)
    fetch_url = _fetch_url(raw_url)
    sent = False
    if fetch_url:
        body, ct = await _fetch_media_bytes(fetch_url)
        if body and len(body) > 0:
            kind = _media_kind(fetch_url, ct)
            fname = _filename_from_url(fetch_url, "file.bin")
            try:
                if kind == "video":
                    await message.answer_video(
                        video=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode=parse_mode,
                    )
                elif kind == "photo":
                    await message.answer_photo(
                        photo=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode=parse_mode,
                    )
                else:
                    await message.answer_document(
                        document=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode=parse_mode,
                    )
                sent = True
            except Exception:
                logging.exception("Send media by bytes failed, trying URL")
        if not sent:
            media_url = _media_url(raw_url)
            if media_url:
                try:
                    kind = _media_kind(media_url)
                    if kind == "video":
                        await message.answer_video(video=media_url, caption=text, parse_mode=parse_mode)
                    elif kind == "photo":
                        await message.answer_photo(photo=media_url, caption=text, parse_mode=parse_mode)
                    else:
                        await message.answer_document(document=media_url, caption=text, parse_mode=parse_mode)
                    sent = True
                except Exception:
                    logging.exception("Failed to send media by URL, falling back to text")
    if not sent:
        await message.answer(text, parse_mode=parse_mode)


async def render_content(message: Message, model, title: str, *, user_id: int | None = None) -> None:
    if not message:
        return
    if user_id is None:
        user_id = getattr(message.from_user, "id", None)
    if user_id is None:
        logging.warning("render_content: no user_id")
        return
    user_id = int(user_id)
    try:
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await message.answer("Сначала выполните регистрацию через /start")
                return
            if user.deleted_at is not None:
                await message.answer("Ваш аккаунт деактивирован. Обратитесь к менеджеру.")
                return
            query = (
                select(model)
                .where(
                    and_(
                        model.is_active.is_(True),
                        or_(model.user_type == user.user_type, model.user_type == UserType.ALL),
                    )
                )
                .order_by(model.published_at.desc().nullslast(), model.created_at.desc())
            )
            items = list((await session.scalars(query.limit(PAGE_SIZE + 1))).all())
            logging.info(
                "Content %s: user_id=%s user_type=%s items=%s",
                model.__tablename__,
                user_id,
                getattr(user.user_type, "value", user.user_type),
                len(items),
            )
    except SQLAlchemyError as e:
        logging.exception("Database error while loading content: %s", e)
        await message.answer("Не удалось получить данные. Попробуйте позже.")
        return
    if not items:
        await message.answer(f"<b>{title}</b>\nПока нет актуальных записей.", parse_mode="HTML")
        return
    await message.answer(f"<b>{title}</b>", parse_mode="HTML")
    has_more = len(items) > PAGE_SIZE
    for item in items[:PAGE_SIZE]:
        await _send_content_item(message, item)
    if has_more:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Показать ещё",
                        callback_data=f"content_more:{model.__tablename__}:{PAGE_SIZE}",
                    )
                ]
            ]
        )
        await message.answer("Загрузить следующую порцию:", reply_markup=kb)


async def render_content_more(
    message: Message,
    model,
    title: str,
    *,
    user_id: int | None = None,
    offset: int = 0,
) -> bool:
    """Отправляет следующую порцию контента и кнопку для продолжения."""
    if not message:
        return False
    if user_id is None:
        user_id = getattr(message.from_user, "id", None)
    if user_id is None:
        logging.warning("render_content_more: no user_id")
        return False
    user_id = int(user_id)
    offset = max(0, int(offset))
    try:
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await message.answer("Сначала выполните регистрацию через /start")
                return False
            if user.deleted_at is not None:
                await message.answer("Ваш аккаунт деактивирован. Обратитесь к менеджеру.")
                return False
            query = (
                select(model)
                .where(
                    and_(
                        model.is_active.is_(True),
                        or_(model.user_type == user.user_type, model.user_type == UserType.ALL),
                    )
                )
                .order_by(model.published_at.desc().nullslast(), model.created_at.desc())
                .offset(offset)
                .limit(PAGE_SIZE + 1)
            )
            items = list((await session.scalars(query)).all())
    except SQLAlchemyError as e:
        logging.exception("Database error while loading content more: %s", e)
        await message.answer("Не удалось получить данные. Попробуйте позже.")
        return False
    if not items:
        await message.answer(f"<b>{title}</b>\nБольше записей нет.", parse_mode="HTML")
        return False
    has_more = len(items) > PAGE_SIZE
    for item in items[:PAGE_SIZE]:
        await _send_content_item(message, item)
    if has_more:
        next_offset = offset + PAGE_SIZE
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Показать ещё",
                        callback_data=f"content_more:{model.__tablename__}:{next_offset}",
                    )
                ]
            ]
        )
        await message.answer("Загрузить следующую порцию:", reply_markup=kb)
    return has_more


def _event_registration_keyboard(event_id: int, user_registered: bool, places_left: bool) -> InlineKeyboardMarkup | None:
    """Клавиатура под мероприятием: Записаться / Вы записаны + Отменить / без кнопки если мест нет."""
    if user_registered:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"event_unreg_{event_id}")],
            ]
        )
    if not places_left:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Записаться", callback_data=f"event_reg_{event_id}")],
        ]
    )


async def _send_event_item(
    message: Message,
    event: Event,
    *,
    registered_count: int = 0,
    user_registered: bool = False,
) -> None:
    safe_title = html.escape(str(event.title))
    safe_desc = html.escape(str(event.description or ""))
    safe_location = html.escape(str(event.location or ""))
    date_str = event.event_date.strftime("%d.%m.%Y, %H:%M") if event.event_date else ""
    header = f"<b>{safe_title}</b>\n📅 {date_str}\n📍 {safe_location}\n\n"
    text = header + safe_desc
    max_places = getattr(event, "max_places", None)
    if max_places is not None:
        places_left = registered_count < max_places
        if not places_left and not user_registered:
            text += "\n\n⚠️ <i>Мест нет.</i>"
        elif max_places > 0:
            text += f"\n\n👥 Мест: {registered_count}/{max_places}"
    if len(text) > 4096:
        text = text[:4090] + "..."
    keyboard = _event_registration_keyboard(
        event.id,
        user_registered=user_registered,
        places_left=max_places is None or registered_count < max_places,
    )
    raw_url = getattr(event, "image_url", None)
    fetch_url = _fetch_url(raw_url)
    sent = False
    if fetch_url:
        body, ct = await _fetch_media_bytes(fetch_url)
        if body and len(body) > 0:
            kind = _media_kind(fetch_url, ct)
            fname = _filename_from_url(fetch_url, "file.bin")
            try:
                if kind == "video":
                    await message.answer_video(
                        video=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                elif kind == "photo":
                    await message.answer_photo(
                        photo=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                else:
                    await message.answer_document(
                        document=BufferedInputFile(file=body, filename=fname),
                        caption=text,
                        parse_mode="HTML",
                        reply_markup=keyboard,
                    )
                sent = True
            except Exception:
                logging.exception("Send event media by bytes failed, trying URL")
        if not sent:
            media_url = _media_url(raw_url)
            if media_url:
                try:
                    kind = _media_kind(media_url)
                    if kind == "video":
                        await message.answer_video(
                            video=media_url, caption=text, parse_mode="HTML", reply_markup=keyboard
                        )
                    elif kind == "photo":
                        await message.answer_photo(
                            photo=media_url, caption=text, parse_mode="HTML", reply_markup=keyboard
                        )
                    else:
                        await message.answer_document(
                            document=media_url, caption=text, parse_mode="HTML", reply_markup=keyboard
                        )
                    sent = True
                except Exception:
                    logging.exception("Failed to send event media by URL, falling back to text")
    if not sent:
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


async def render_events(message: Message, *, user_id: int | None = None) -> None:
    if not message:
        return
    if user_id is None:
        user_id = getattr(message.from_user, "id", None)
    if user_id is None:
        logging.warning("render_events: no user_id")
        return
    user_id = int(user_id)
    try:
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await message.answer("Сначала выполните регистрацию через /start")
                return
            if user.deleted_at is not None:
                await message.answer("Ваш аккаунт деактивирован. Обратитесь к менеджеру.")
                return
            now = datetime.utcnow()
            query = (
                select(Event)
                .where(
                    and_(
                        Event.is_active.is_(True),
                        Event.event_date >= now,
                        or_(Event.user_type == user.user_type, Event.user_type == UserType.ALL),
                    )
                )
                .order_by(Event.event_date.asc())
            )
            events = list((await session.scalars(query.limit(PAGE_SIZE + 1))).all())
            logging.info(
                "Events: user_id=%s user_type=%s count=%s",
                user_id,
                getattr(user.user_type, "value", user.user_type),
                len(events),
            )
            user_type_label = "HoReCa" if user.user_type == UserType.HORECA else "Retail"
            if not events:
                await message.answer(
                    "🎪 <b>МЕРОПРИЯТИЯ</b>\n\n"
                    "На данный момент нет запланированных мероприятий. Следите за анонсами!\n\n"
                    "Обычно мы проводим:\n"
                    "• Дегустации новых вкусов\n"
                    "• Тренинги для кальянщиков\n"
                    "• Партнерские встречи\n"
                    "• Презентации новинок",
                    parse_mode="HTML",
                )
                return
            await message.answer(
                f"🎪 <b>ПРЕДСТОЯЩИЕ МЕРОПРИЯТИЯ</b>\nдля {user_type_label}\n\n─────────────────",
                parse_mode="HTML",
            )
            has_more = len(events) > PAGE_SIZE
            for event in events[:PAGE_SIZE]:
                reg_count = await session.scalar(
                    select(func.count())
                    .select_from(EventRegistration)
                    .where(EventRegistration.event_id == event.id)
                )
                user_reg = await session.scalar(
                    select(EventRegistration).where(
                        EventRegistration.event_id == event.id,
                        EventRegistration.user_id == user_id,
                    )
                )
                await _send_event_item(
                    message,
                    event,
                    registered_count=reg_count or 0,
                    user_registered=user_reg is not None,
                )
            if has_more:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Показать ещё", callback_data=f"events_more:{PAGE_SIZE}")]
                    ]
                )
                await message.answer("Загрузить следующую порцию:", reply_markup=kb)
    except SQLAlchemyError as e:
        logging.exception("Database error while loading events: %s", e)
        await message.answer("Не удалось получить данные. Попробуйте позже.")


async def render_events_more(message: Message, *, user_id: int | None = None, offset: int = 0) -> bool:
    """Отправляет следующую порцию мероприятий и кнопку продолжения."""
    if not message:
        return False
    if user_id is None:
        user_id = getattr(message.from_user, "id", None)
    if user_id is None:
        logging.warning("render_events_more: no user_id")
        return False
    user_id = int(user_id)
    offset = max(0, int(offset))
    try:
        async with SessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await message.answer("Сначала выполните регистрацию через /start")
                return False
            if user.deleted_at is not None:
                await message.answer("Ваш аккаунт деактивирован. Обратитесь к менеджеру.")
                return False
            now = datetime.utcnow()
            query = (
                select(Event)
                .where(
                    and_(
                        Event.is_active.is_(True),
                        Event.event_date >= now,
                        or_(Event.user_type == user.user_type, Event.user_type == UserType.ALL),
                    )
                )
                .order_by(Event.event_date.asc())
                .offset(offset)
                .limit(PAGE_SIZE + 1)
            )
            events = list((await session.scalars(query)).all())
            if not events:
                await message.answer("Больше мероприятий нет.")
                return False
            has_more = len(events) > PAGE_SIZE
            for event in events[:PAGE_SIZE]:
                reg_count = await session.scalar(
                    select(func.count())
                    .select_from(EventRegistration)
                    .where(EventRegistration.event_id == event.id)
                )
                user_reg = await session.scalar(
                    select(EventRegistration).where(
                        EventRegistration.event_id == event.id,
                        EventRegistration.user_id == user_id,
                    )
                )
                await _send_event_item(
                    message,
                    event,
                    registered_count=reg_count or 0,
                    user_registered=user_reg is not None,
                )
            if has_more:
                next_offset = offset + PAGE_SIZE
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Показать ещё", callback_data=f"events_more:{next_offset}")]
                    ]
                )
                await message.answer("Загрузить следующую порцию:", reply_markup=kb)
            return has_more
    except SQLAlchemyError as e:
        logging.exception("Database error while loading events more: %s", e)
        await message.answer("Не удалось получить данные. Попробуйте позже.")
        return False
