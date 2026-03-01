import html
import logging
from urllib.parse import urlparse

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime

from config.settings import get_settings
from database.models import Event, EventRegistration, User, UserType
from database.session import SessionLocal

settings = get_settings()


def _media_url(url: str | None) -> str | None:
    """Возвращает URL медиа, доступный для Telegram. Подменяет localhost на UPLOAD_PUBLIC_BASE_URL при необходимости."""
    if not url or not url.strip():
        return None
    u = url.strip()
    if u.startswith(("http://", "https://")):
        final = u
    else:
        base = (settings.upload_base_url or "").rstrip("/")
        path = u if u.startswith("/") else f"/{u}"
        final = f"{base}{path}" if base else None
    if not final:
        return None
    # Telegram не может загрузить файл по localhost — подменяем origin на публичный (хост:порт)
    public_base = getattr(settings, "upload_public_base_url", None)
    if public_base and "localhost" in final:
        try:
            parsed = urlparse(final)
            path = parsed.path or "/"
            query = f"?{parsed.query}" if parsed.query else ""
            base = public_base.rstrip("/")
            return f"{base}{path}{query}"
        except Exception as e:
            logging.warning("Failed to rewrite media URL with public base: %s", e)
    return final


def _is_video_url(url: str) -> bool:
    lower = url.lower()
    return any(lower.endswith(ext) for ext in (".mp4", ".webm", ".mov"))


async def _send_content_item(message: Message, item, parse_mode: str = "HTML") -> None:
    safe_title = html.escape(str(item.title))
    safe_desc = html.escape(str(item.description or ""))
    text = f"<b>{safe_title}</b>\n\n{safe_desc}"
    if len(text) > 4096:
        text = text[:4090] + "..."
    media_url = _media_url(item.image_url)
    if media_url:
        try:
            if _is_video_url(media_url):
                await message.answer_video(video=media_url, caption=text, parse_mode=parse_mode)
            else:
                await message.answer_photo(photo=media_url, caption=text, parse_mode=parse_mode)
        except Exception:
            logging.exception("Failed to send media, falling back to text")
            await message.answer(text, parse_mode=parse_mode)
    else:
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
            items = list((await session.scalars(query)).all())
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
    for item in items[:5]:
        await _send_content_item(message, item)


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
    media_url = _media_url(event.image_url)
    if media_url:
        try:
            if _is_video_url(media_url):
                await message.answer_video(
                    video=media_url, caption=text, parse_mode="HTML", reply_markup=keyboard
                )
            else:
                await message.answer_photo(
                    photo=media_url, caption=text, parse_mode="HTML", reply_markup=keyboard
                )
        except Exception:
            logging.exception("Failed to send event media, falling back to text")
            await message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
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
            events = list((await session.scalars(query)).all())
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
            for event in events[:5]:
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
    except SQLAlchemyError as e:
        logging.exception("Database error while loading events: %s", e)
        await message.answer("Не удалось получить данные. Попробуйте позже.")
