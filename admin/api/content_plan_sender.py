"""
Отправка записей контент-плана в бот и каналы Telegram.
Используется воркером по расписанию и может вызываться из тестов с mock telegram_sender.
"""
import asyncio
import html
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api import telegram_sender as tg
from config.settings import get_settings
from database.models import (
    ContentPlan,
    ContentPlanChannel,
    ContentPlanItem,
    Delivery,
    DistributionChannel,
    DistributionChannelType,
    Event,
    News,
    Promotion,
    TelegramDeliveryLog,
    User,
)

logger = logging.getLogger(__name__)


def _escape(s: str | None) -> str:
    if not s:
        return ""
    return html.escape(str(s))


def _normalize_html_for_telegram(html: str | None) -> str:
    """Санитизирует HTML для Telegram: <p>→переносы, rel/target убираем. Telegram не поддерживает <br>, используем \\n."""
    from admin.api.html_sanitizer import sanitize_html_for_telegram

    if not html or not html.strip():
        return ""
    cleaned = sanitize_html_for_telegram(html)
    cleaned = cleaned.replace("</p>", "\n").replace("<p>", "").strip()
    cleaned = re.sub(r'\s+rel="[^"]*"', "", cleaned)
    cleaned = re.sub(r'\s+target="[^"]*"', "", cleaned)
    # Telegram HTML не поддерживает <br> — заменяем на \n
    cleaned = re.sub(r'<br\s*/?>', "\n", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _content_type_value(ct: Any) -> str:
    return ct.value if hasattr(ct, "value") else ct


def _event_registration_reply_markup(event_id: int) -> dict:
    """Кнопка «Записаться» под мероприятием (callback_data как в боте)."""
    return {
        "inline_keyboard": [
            [{"text": "✅ Записаться", "callback_data": f"event_reg_{event_id}"}],
        ],
    }


async def get_plan_message(db: AsyncSession, plan: ContentPlan) -> tuple[str, str, str | None, int | None]:
    """
    Возвращает (title, description, media_url, event_id) для плана.
    event_id не None только когда content_type == event и content_id задан.
    """
    if plan.content_type == "custom" or _content_type_value(plan.content_type) == "custom":
        return (
            _escape(plan.custom_title) or "Рассылка",
            _normalize_html_for_telegram(plan.custom_description) or "",
            plan.custom_media_url.strip() if plan.custom_media_url else None,
            None,
        )
    if not plan.content_id:
        return (_escape(plan.title), "", None, None)
    model_map = {
        "promotion": Promotion,
        "news": News,
        "delivery": Delivery,
        "event": Event,
    }
    ct = _content_type_value(plan.content_type)
    model = model_map.get(ct)
    if not model:
        return (_escape(plan.title), "", None, None)
    item = await db.get(model, plan.content_id)
    if not item:
        return (_escape(plan.title), "", None, None)
    title = getattr(item, "title", None) or plan.title
    desc = getattr(item, "description", None) or ""
    media = getattr(item, "image_url", None)
    event_id = int(plan.content_id) if ct == "event" else None
    return (
        _escape(title),
        _normalize_html_for_telegram(desc),
        (media.strip() if media else None) or None,
        event_id,
    )


async def get_item_message(db: AsyncSession, item: ContentPlanItem) -> tuple[str, str, str | None, int | None]:
    """Возвращает (title, description, media_url, event_id) для одного пункта плана. event_id не None только для типа event."""
    if _content_type_value(item.content_type) == "custom":
        return (
            _escape(item.custom_title) or "Сообщение",
            _normalize_html_for_telegram(item.custom_description) or "",
            item.custom_media_url.strip() if item.custom_media_url else None,
            None,
        )
    if not item.content_id:
        return (_escape(item.custom_title) or "Сообщение", "", None, None)
    ct = _content_type_value(item.content_type)
    model_map = {
        "promotion": Promotion,
        "news": News,
        "delivery": Delivery,
        "event": Event,
    }
    model = model_map.get(ct)
    if not model:
        return (_escape(item.custom_title) or "Сообщение", "", None, None)
    entity = await db.get(model, item.content_id)
    if not entity:
        return (_escape(item.custom_title) or "Сообщение", "", None, None)
    title = getattr(entity, "title", None) or item.custom_title or "Сообщение"
    desc = getattr(entity, "description", None) or ""
    media = getattr(entity, "image_url", None)
    event_id = int(item.content_id) if ct == "event" else None
    return (
        _escape(title),
        _normalize_html_for_telegram(desc),
        (media.strip() if media else None) or None,
        event_id,
    )


def _build_text(title: str, description: str) -> str:
    if not description:
        return f"<b>{title}</b>"
    return f"<b>{title}</b>\n\n{description}"[:4096]


def _is_internal_media_host(netloc: str) -> bool:
    """Хост, до которого Telegram с интернета не достучится."""
    if not netloc:
        return True
    host = netloc.split(":")[0].lower()
    if host in ("localhost", "127.0.0.1", "api", "backend", "app", "minio"):
        return True
    if "localhost" in host or host.startswith("127."):
        return True
    return False


def _ensure_public_media_url(url: str | None) -> str | None:
    """
    Преобразует URL медиа в публичный, доступный для Telegram.
    Логика как в bot.utils._media_url: относительные пути и внутренние хосты (api, minio, localhost) → base + path.
    """
    if not url or not url.strip():
        return None
    u = url.strip()
    st = get_settings()
    base = None
    if st.use_s3 and st.s3_public_base_url:
        base = st.s3_public_base_url.rstrip("/")
    elif st.upload_public_base_url:
        base = st.upload_public_base_url.rstrip("/")
    if not base:
        return u
    if u.startswith(("http://", "https://")):
        if u.startswith(base):
            return u
        try:
            parsed = urlparse(u)
            if not _is_internal_media_host(parsed.netloc or ""):
                return u
            path = parsed.path or "/"
            query = f"?{parsed.query}" if parsed.query else ""
            return f"{base}{path}{query}"
        except Exception:
            return u
    path = u if u.startswith("/") else f"/{u}"
    return f"{base}{path}"


def _is_video_url(url: str) -> bool:
    """Проверка: URL указывает на видео (sendPhoto не подходит, нужен sendVideo)."""
    lower = (url or "").lower()
    return any(lower.endswith(ext) for ext in (".mp4", ".webm", ".mov"))


def _is_image_url(url: str) -> bool:
    """Форматы, которые отправляем как фото."""
    lower = (url or "").lower()
    return any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp"))


def _media_kind(url: str, content_type: str = "") -> str:
    """'video' | 'photo' | 'document' — как отправлять файл в контент-плане."""
    if _is_video_url(url):
        return "video"
    if _is_image_url(url):
        return "photo"
    ct = (content_type or "").lower()
    if ct.startswith("video/"):
        return "video"
    if ct.startswith("image/"):
        return "photo"
    return "document"


async def _fetch_media_bytes(url: str) -> tuple[bytes | None, str, str]:
    """
    Скачать медиа по URL. Возвращает (bytes, filename, content_type) или (None, "", "").
    Для нашего S3 использует boto3 (работает с приватным bucket).
    """
    if not url or not url.strip():
        return None, "", ""
    url = url.strip()
    st = get_settings()
    # Наш S3: используем boto3 (работает даже с приватным bucket)
    if st.use_s3 and st.s3_public_base_url and url.startswith(st.s3_public_base_url.rstrip("/")):
        try:
            import boto3
            from botocore.config import Config

            prefix = st.s3_public_base_url.rstrip("/") + "/"
            key = url[len(prefix):] if url.startswith(prefix) else url.split("/", 3)[-1]
            bucket = st.s3_bucket or ""
            config = Config(signature_version="s3v4", s3={"addressing_style": "path"})
            client_kw = {
                "service_name": "s3",
                "aws_access_key_id": st.s3_access_key_id,
                "aws_secret_access_key": st.s3_secret_access_key,
                "config": config,
            }
            if st.s3_region:
                client_kw["region_name"] = st.s3_region
            if st.s3_endpoint_url:
                client_kw["endpoint_url"] = st.s3_endpoint_url

            def _get():
                c = boto3.client(**client_kw)
                obj = c.get_object(Bucket=bucket, Key=key)
                return obj["Body"].read(), obj.get("ContentType") or "application/octet-stream"

            loop = asyncio.get_running_loop()
            body, ct = await loop.run_in_executor(None, _get)
            filename = key.split("/")[-1] if "/" in key else key
            return body, filename, ct
        except Exception as e:
            logger.warning("S3 fetch failed for %s: %s", url[:80], e)
            return None, "", ""
    # Внешний URL: HTTP GET
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return None, "", ""
            ct = (r.headers.get("content-type") or "application/octet-stream").split(";")[0].strip()
            if "text/html" in ct:
                return None, "", ""
            filename = url.split("/")[-1].split("?")[0] or "photo.jpg"
            return r.content, filename, ct
    except Exception as e:
        logger.warning("HTTP fetch failed for %s: %s", url[:80], e)
        return None, "", ""


def _normalize_channel_ref(ref: str) -> str:
    """Из ссылки t.me/username или telegram.me/username извлекает @username. Иначе возвращает ref как есть."""
    ref = (ref or "").strip()
    if not ref:
        return ref
    for prefix in ("https://t.me/", "http://t.me/", "t.me/", "https://telegram.me/", "http://telegram.me/", "telegram.me/"):
        if ref.lower().startswith(prefix) or prefix in ref:
            rest = ref.split(prefix, 1)[-1].split("?")[0].split("/")[0].strip()
            if rest:
                return f"@{rest}" if not rest.startswith("@") else rest
            break
    return ref


async def _send_one_message(
    db: AsyncSession,
    bot_token: str,
    rows: list,
    title: str,
    description: str,
    media_url: str | None,
    *,
    event_id: int | None = None,
    plan_id: int,
    plan_title: str,
    admin_id: int | None = None,
    telegram_client: httpx.AsyncClient | None = None,
) -> tuple[int, int, list[str]]:
    """Отправить одно сообщение (title, description, media) во все каналы из rows. Если event_id задан — под сообщением кнопка «Записаться»."""
    text = _build_text(title, description)
    reply_markup = _event_registration_reply_markup(event_id) if event_id is not None else None
    media_url_public = _ensure_public_media_url(media_url)
    kind = _media_kind(media_url or media_url_public or "", "")
    if media_url_public:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                r = await client.head(media_url_public)
                ct = (r.headers.get("content-type") or "").lower()
                if r.status_code != 200:
                    logger.warning("Media pre-check status=%s, will try send anyway: %s", r.status_code, media_url_public[:80])
                elif "text/html" in ct:
                    logger.warning("Media URL returns HTML (likely error page), sending text only: %s", media_url_public[:80])
                    media_url_public = None
        except Exception as e:
            logger.warning("Media pre-check failed (will try send anyway): %s url=%s", e, media_url_public[:80])
    sent_bot = 0
    sent_channel = 0
    errors: list[str] = []

    def _log(chan_type: str, target: str, success: bool, err: str | None = None) -> None:
        db.add(
            TelegramDeliveryLog(
                plan_id=plan_id,
                plan_title=plan_title,
                channel_type=chan_type,
                target=target,
                success=success,
                error_message=err,
                admin_id=admin_id,
            )
        )

    def _is_wrong_type_error(err: str | None) -> bool:
        return err is not None and (
            "wrong type of the web page content" in err.lower()
            or "type of file mismatch" in err.lower()
        )

    async def _send_media(chat_id: str | int) -> tuple[bool, str | None]:
        """Отправить медиа: сначала по URL, при ошибке — скачать и отправить файлом (video/photo/document)."""
        if not media_url_public:
            return False, None
        if kind == "video":
            result, err = await tg.send_video(
                bot_token, chat_id, media_url_public, caption=text, reply_markup=reply_markup, client=telegram_client
            )
        elif kind == "photo":
            result, err = await tg.send_photo(
                bot_token, chat_id, media_url_public, caption=text, reply_markup=reply_markup, client=telegram_client
            )
        else:
            result, err = await tg.send_document(
                bot_token, chat_id, media_url_public, caption=text, reply_markup=reply_markup, client=telegram_client
            )
        if result:
            return True, None
        if _is_wrong_type_error(err) and kind == "photo":
            result, err = await tg.send_video(
                bot_token, chat_id, media_url_public, caption=text, reply_markup=reply_markup, client=telegram_client
            )
            if result:
                return True, None
        # Fallback: скачать и отправить файлом (работает с приватным S3 и любым типом)
        logger.info("URL send failed, trying fetch+send: %s", err[:60] if err else "")
        body, fname, ct = await _fetch_media_bytes(media_url_public)
        if body and len(body) > 0:
            if kind == "video":
                result, err = await tg.send_video_by_bytes(
                    bot_token, chat_id, body, fname or "video.mp4", ct or "video/mp4",
                    caption=text, reply_markup=reply_markup, client=telegram_client
                )
            elif kind == "photo":
                result, err = await tg.send_photo_by_bytes(
                    bot_token, chat_id, body, fname or "photo.jpg", ct or "image/jpeg",
                    caption=text, reply_markup=reply_markup, client=telegram_client
                )
            else:
                result, err = await tg.send_document_by_bytes(
                    bot_token, chat_id, body, fname or "document.bin",
                    caption=text, reply_markup=reply_markup, client=telegram_client
                )
            if result:
                return True, None
        return False, err

    for ch in rows:
        if ch.channel_type == DistributionChannelType.BOT:
            users = list((await db.scalars(select(User.id).where(User.is_active.is_(True), User.deleted_at.is_(None)))).all())
            for uid in users:
                if media_url_public:
                    ok, err_msg = await _send_media(uid)
                    if not ok:
                        txt_resp, err_msg = await tg.send_text(
                            bot_token, uid, text, reply_markup=reply_markup, client=telegram_client
                        )
                        result = txt_resp is not None
                    else:
                        result = True
                else:
                    txt_resp, err_msg = await tg.send_text(
                        bot_token, uid, text, reply_markup=reply_markup, client=telegram_client
                    )
                    result = txt_resp is not None
                target = f"user:{uid}"
                if result:
                    sent_bot += 1
                    _log("bot", target, True)
                else:
                    errors.append(f"bot user {uid}" + (f": {err_msg}" if err_msg else ""))
                    _log("bot", target, False, err_msg)
        elif ch.channel_type == DistributionChannelType.TELEGRAM_CHANNEL and ch.telegram_ref:
            chat = _normalize_channel_ref(ch.telegram_ref)
            if media_url_public:
                ok, err_msg = await _send_media(chat)
                if not ok:
                    txt_resp, err_msg = await tg.send_text(
                        bot_token, chat, text, reply_markup=reply_markup, client=telegram_client
                    )
                    result = txt_resp is not None
                else:
                    result = True
            else:
                txt_resp, err_msg = await tg.send_text(
                    bot_token, chat, text, reply_markup=reply_markup, client=telegram_client
                )
                result = txt_resp is not None
            target = chat
            if result:
                sent_channel += 1
                _log("telegram_channel", target, True)
            else:
                errors.append(f"канал {chat}" + (f": {err_msg}" if err_msg else ""))
                _log("telegram_channel", target, False, err_msg)
    return sent_bot, sent_channel, errors


async def send_plan_to_telegram(
    db: AsyncSession,
    plan: ContentPlan,
    bot_token: str,
    *,
    admin_id: int | None = None,
    telegram_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """
    Отправить контент плана во все привязанные каналы.
    Если у плана есть пункты (items) — отправляет по очереди все сообщения с разными типами.
    Иначе — одно сообщение из полей плана.
    Возвращает {"sent_bot": N, "sent_channel": M, "errors": [...]}.
    """
    if telegram_client is None:
        async with httpx.AsyncClient(**tg.telegram_http_kwargs(120.0)) as c:
            return await send_plan_to_telegram(db, plan, bot_token, admin_id=admin_id, telegram_client=c)
    rows = (
        await db.execute(
            select(DistributionChannel)
            .join(ContentPlanChannel, ContentPlanChannel.channel_id == DistributionChannel.id)
            .where(
                ContentPlanChannel.plan_id == plan.id,
                DistributionChannel.is_active.is_(True),
            )
        )
    ).scalars().all()
    channels_count = len(rows)
    sent_bot = 0
    sent_channel = 0
    errors: list[str] = []

    items = (
        await db.execute(
            select(ContentPlanItem).where(ContentPlanItem.plan_id == plan.id).order_by(ContentPlanItem.sort_order)
        )
    ).scalars().all()

    plan_id = plan.id
    plan_title = (plan.title or "План")[:255]
    send_kw = {"plan_id": plan_id, "plan_title": plan_title, "admin_id": admin_id, "telegram_client": telegram_client}

    if items:
        # Несколько сообщений в плане: отправляем по порядку
        for row in items:
            item_entity = row[0]
            title, description, media_url, event_id = await get_item_message(db, item_entity)
            sb, sc, errs = await _send_one_message(
                db, bot_token, rows, title, description, media_url, event_id=event_id, **send_kw
            )
            sent_bot += sb
            sent_channel += sc
            errors.extend(errs)
    else:
        # Одно сообщение из полей плана (как раньше)
        title, description, media_url, event_id = await get_plan_message(db, plan)
        sent_bot, sent_channel, errors = await _send_one_message(
            db, bot_token, rows, title, description, media_url, event_id=event_id, **send_kw
        )

    return {"sent_bot": sent_bot, "sent_channel": sent_channel, "errors": errors, "channels_count": channels_count}


async def process_due_content_plans(db: AsyncSession, bot_token: str) -> int:
    """
    Найти планы со status=scheduled и scheduled_at <= now, отправить в каналы, обновить status=sent.
    Возвращает количество обработанных планов.
    """
    from database.models import ContentPlanStatus

    now = datetime.utcnow()
    due = list(
        (
            await db.scalars(
                select(ContentPlan).where(
                    ContentPlan.status == ContentPlanStatus.SCHEDULED,
                    ContentPlan.scheduled_at.is_not(None),
                    ContentPlan.scheduled_at <= now,
                )
            )
        ).all()
    )
    for plan in due:
        try:
            result = await send_plan_to_telegram(db, plan, bot_token)
            plan.status = ContentPlanStatus.SENT
            plan.sent_at = now
            db.add(plan)
            await db.commit()
            logger.info(
                "Content plan %s sent: bot=%s channel=%s errors=%s",
                plan.id,
                result["sent_bot"],
                result["sent_channel"],
                result["errors"],
            )
        except Exception as e:
            await db.rollback()
            logger.exception("Content plan %s send failed: %s", plan.id, e)
    return len(due)
