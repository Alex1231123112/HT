"""Загрузка медиа из бота на сервер (для разрешённых Telegram ID)."""

import logging

import httpx
from aiogram import Bot, F, Router
from aiogram.types import Document, Message, PhotoSize

from config.settings import get_settings

router = Router()
logger = logging.getLogger(__name__)


def _allowed_telegram_ids() -> set[int]:
    raw = getattr(get_settings(), "bot_upload_allowed_telegram_ids", None) or ""
    if not raw.strip():
        return set()
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}


async def _download_file_bytes(bot: Bot, file_id: str) -> bytes:
    tg_file = await bot.get_file(file_id)
    buf = await bot.download_file(tg_file.file_path)
    buf.seek(0)
    return buf.read()


async def _upload_to_api(content: bytes, filename: str) -> str | None:
    settings = get_settings()
    secret = getattr(settings, "bot_upload_secret", None) or ""
    if not secret:
        return None
    base = (getattr(settings, "api_base_url", None) or "http://localhost:8000").rstrip("/")
    url = f"{base}/api/upload-from-bot"
    headers = {"X-Bot-Upload-Secret": secret}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                url,
                files={"file": (filename, content)},
                headers=headers,
            )
            if resp.status_code != 200:
                logger.warning("upload-from-bot status %s: %s", resp.status_code, resp.text)
                return None
            data = resp.json()
            url_returned = (data.get("data") or {}).get("url")
            return url_returned
    except Exception as e:
        logger.exception("upload-from-bot request failed: %s", e)
        return None


@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    allowed = _allowed_telegram_ids()
    if not allowed or message.from_user is None or message.from_user.id not in allowed:
        return
    photo: PhotoSize = message.photo[-1]
    try:
        content = await _download_file_bytes(bot, photo.file_id)
        filename = f"{photo.file_id}.jpg"
        url = await _upload_to_api(content, filename)
        if url:
            await message.reply(
                f"✅ Файл загружен на сервер.\n\nСсылка для контента (вставьте в админке в поле «Ссылка на медиа»):\n{url}"
            )
        else:
            await message.reply("❌ Не удалось загрузить файл. Проверьте BOT_UPLOAD_SECRET и API_BASE_URL в .env.")
    except Exception as e:
        logger.exception("Photo upload failed: %s", e)
        await message.reply("❌ Ошибка загрузки.")


@router.message(F.document)
async def handle_document(message: Message, bot: Bot) -> None:
    allowed = _allowed_telegram_ids()
    if not allowed or message.from_user is None or message.from_user.id not in allowed:
        return
    doc: Document = message.document
    if doc.file_size and doc.file_size > 5 * 1024 * 1024:
        await message.reply("❌ Файл не больше 5 МБ.")
        return
    try:
        content = await _download_file_bytes(bot, doc.file_id)
        filename = doc.file_name or f"{doc.file_id}.bin"
        url = await _upload_to_api(content, filename)
        if url:
            await message.reply(
                f"✅ Файл загружен на сервер.\n\nСсылка для контента:\n{url}"
            )
        else:
            await message.reply("❌ Не удалось загрузить файл. Проверьте BOT_UPLOAD_SECRET и API_BASE_URL в .env.")
    except Exception as e:
        logger.exception("Document upload failed: %s", e)
        await message.reply("❌ Ошибка загрузки.")
