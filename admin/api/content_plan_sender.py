"""
Отправка записей контент-плана в бот и каналы Telegram.
Используется воркером по расписанию и может вызываться из тестов с mock telegram_sender.
"""
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


async def get_plan_message(db: AsyncSession, plan: ContentPlan) -> tuple[str, str, str | None]:
    """
    Возвращает (title, description, media_url) для плана.
    Загружает контент по content_type/content_id или использует custom_*.
    """
    if plan.content_type == "custom" or _content_type_value(plan.content_type) == "custom":
        return (
            _escape(plan.custom_title) or "Рассылка",
            _normalize_html_for_telegram(plan.custom_description) or "",
            plan.custom_media_url.strip() if plan.custom_media_url else None,
        )
    if not plan.content_id:
        return (_escape(plan.title), "", None)
    model_map = {
        "promotion": Promotion,
        "news": News,
        "delivery": Delivery,
        "event": Event,
    }
    model = model_map.get(_content_type_value(plan.content_type))
    if not model:
        return (_escape(plan.title), "", None)
    item = await db.get(model, plan.content_id)
    if not item:
        return (_escape(plan.title), "", None)
    title = getattr(item, "title", None) or plan.title
    desc = getattr(item, "description", None) or ""
    media = getattr(item, "image_url", None)
    return (_escape(title), _normalize_html_for_telegram(desc), (media.strip() if media else None) or None)


async def get_item_message(db: AsyncSession, item: ContentPlanItem) -> tuple[str, str, str | None]:
    """Возвращает (title, description, media_url) для одного пункта плана (ContentPlanItem)."""
    if _content_type_value(item.content_type) == "custom":
        return (
            _escape(item.custom_title) or "Сообщение",
            _normalize_html_for_telegram(item.custom_description) or "",
            item.custom_media_url.strip() if item.custom_media_url else None,
        )
    if not item.content_id:
        return (_escape(item.custom_title) or "Сообщение", "", None)
    model_map = {
        "promotion": Promotion,
        "news": News,
        "delivery": Delivery,
        "event": Event,
    }
    model = model_map.get(_content_type_value(item.content_type))
    if not model:
        return (_escape(item.custom_title) or "Сообщение", "", None)
    entity = await db.get(model, item.content_id)
    if not entity:
        return (_escape(item.custom_title) or "Сообщение", "", None)
    title = getattr(entity, "title", None) or item.custom_title or "Сообщение"
    desc = getattr(entity, "description", None) or ""
    media = getattr(entity, "image_url", None)
    return (_escape(title), _normalize_html_for_telegram(desc), (media.strip() if media else None) or None)


def _build_text(title: str, description: str) -> str:
    if not description:
        return f"<b>{title}</b>"
    return f"<b>{title}</b>\n\n{description}"[:4096]


def _ensure_public_media_url(url: str | None) -> str | None:
    """
    Подменяет localhost/127.0.0.1 в URL медиа на публичный base, чтобы Telegram мог скачать файл.
    В проде API и бот в Docker — Telegram не может обратиться к localhost.
    """
    if not url or not url.strip():
        return None
    u = url.strip()
    if "localhost" not in u and "127.0.0.1" not in u:
        return u
    st = get_settings()
    base = None
    if st.use_s3 and st.s3_public_base_url:
        base = st.s3_public_base_url.rstrip("/")
    elif st.upload_public_base_url:
        base = st.upload_public_base_url.rstrip("/")
    if not base:
        return u
    try:
        parsed = urlparse(u)
        path = parsed.path or "/"
        return f"{base}{path}"
    except Exception:
        return u


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
    plan_id: int,
    plan_title: str,
    admin_id: int | None = None,
    telegram_client: httpx.AsyncClient | None = None,
) -> tuple[int, int, list[str]]:
    """Отправить одно сообщение (title, description, media) во все каналы из rows. Возвращает (sent_bot, sent_channel, errors)."""
    text = _build_text(title, description)
    media_url_public = _ensure_public_media_url(media_url)
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

    for ch in rows:
        if ch.channel_type == DistributionChannelType.BOT:
            users = list((await db.scalars(select(User.id).where(User.is_active.is_(True), User.deleted_at.is_(None)))).all())
            for uid in users:
                if media_url_public:
                    result, err_msg = await tg.send_photo(
                        bot_token, uid, media_url_public, caption=text, client=telegram_client
                    )
                else:
                    result, err_msg = await tg.send_text(bot_token, uid, text, client=telegram_client)
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
                result, err_msg = await tg.send_photo(bot_token, chat, media_url_public, caption=text, client=telegram_client)
            else:
                result, err_msg = await tg.send_text(bot_token, chat, text, client=telegram_client)
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
            title, description, media_url = await get_item_message(db, item_entity)
            sb, sc, errs = await _send_one_message(
                db, bot_token, rows, title, description, media_url, **send_kw
            )
            sent_bot += sb
            sent_channel += sc
            errors.extend(errs)
    else:
        # Одно сообщение из полей плана (как раньше)
        title, description, media_url = await get_plan_message(db, plan)
        sent_bot, sent_channel, errors = await _send_one_message(
            db, bot_token, rows, title, description, media_url, **send_kw
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
            logger.info(
                "Content plan %s sent: bot=%s channel=%s errors=%s",
                plan.id,
                result["sent_bot"],
                result["sent_channel"],
                result["errors"],
            )
        except Exception as e:
            logger.exception("Content plan %s send failed: %s", plan.id, e)
        # продолжаем со следующим планом
    await db.commit()
    return len(due)
