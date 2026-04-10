"""
Отправка сообщений в Telegram (Bot API).
Используется для рассылки в бот (подписчикам) и в каналы.
В тестах можно подставить mock-клиент и проверять вызовы.
"""
import json
import logging
import os
from typing import Any

import httpx

from config.settings import get_settings

TELEGRAM_API = "https://api.telegram.org"
PARSE_MODE_HTML = "HTML"

logger = logging.getLogger(__name__)


def telegram_http_kwargs(timeout: float = 30.0) -> dict[str, Any]:
    """Параметры httpx.AsyncClient для api.telegram.org (TELEGRAM_PROXY / HTTPS_PROXY, как у бота)."""
    settings = get_settings()
    proxy: str | None = None
    if settings.telegram_proxy and settings.telegram_proxy.strip():
        proxy = settings.telegram_proxy.strip()
    else:
        for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
            v = os.environ.get(key)
            if v and v.strip():
                proxy = v.strip()
                break
    kw: dict[str, Any] = {"timeout": timeout}
    if proxy:
        kw["proxy"] = proxy
    return kw


async def send_text(
    bot_token: str,
    chat_id: str | int,
    text: str,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить текстовое сообщение в чат/канал. Возвращает (response_data, None) при успехе или (None, error_message)."""
    url = f"{TELEGRAM_API}/bot{bot_token}/sendMessage"
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text[:4096], "parse_mode": parse_mode}
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    if client is None:
        async with httpx.AsyncClient(**telegram_http_kwargs(30.0)) as c:
            return await _post(c, url, payload)
    return await _post(client, url, payload)


async def send_photo(
    bot_token: str,
    chat_id: str | int,
    photo_url: str,
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить фото по URL в чат/канал. Возвращает (response_data, None) при успехе или (None, error_message)."""
    url = f"{TELEGRAM_API}/bot{bot_token}/sendPhoto"
    payload: dict[str, Any] = {"chat_id": chat_id, "photo": photo_url}
    if caption:
        payload["caption"] = caption[:1024]
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    if client is None:
        async with httpx.AsyncClient(**telegram_http_kwargs(30.0)) as c:
            return await _post(c, url, payload)
    return await _post(client, url, payload)


async def send_video(
    bot_token: str,
    chat_id: str | int,
    video_url: str,
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить видео по URL в чат/канал. Возвращает (response_data, None) при успехе или (None, error_message)."""
    url = f"{TELEGRAM_API}/bot{bot_token}/sendVideo"
    payload: dict[str, Any] = {"chat_id": chat_id, "video": video_url}
    if caption:
        payload["caption"] = caption[:1024]
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    if client is None:
        async with httpx.AsyncClient(**telegram_http_kwargs(60.0)) as c:
            return await _post(c, url, payload)
    return await _post(client, url, payload)


async def send_photo_by_bytes(
    bot_token: str,
    chat_id: str | int,
    file_bytes: bytes,
    filename: str = "photo.jpg",
    content_type: str = "image/jpeg",
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить фото как файл (multipart). Работает когда URL недоступен для Telegram."""
    api_url = f"{TELEGRAM_API}/bot{bot_token}/sendPhoto"
    data: dict[str, Any] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption[:1024]
        data["parse_mode"] = parse_mode
    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)
    files = {"photo": (filename, file_bytes, content_type)}
    return await _post_multipart(client, api_url, data, files)


async def send_video_by_bytes(
    bot_token: str,
    chat_id: str | int,
    file_bytes: bytes,
    filename: str = "video.mp4",
    content_type: str = "video/mp4",
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить видео как файл (multipart). Работает когда URL недоступен для Telegram."""
    api_url = f"{TELEGRAM_API}/bot{bot_token}/sendVideo"
    data: dict[str, Any] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption[:1024]
        data["parse_mode"] = parse_mode
    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)
    files = {"video": (filename, file_bytes, content_type)}
    return await _post_multipart(client, api_url, data, files, timeout=60.0)


async def send_document(
    bot_token: str,
    chat_id: str | int,
    document_url: str,
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить документ по URL в чат/канал."""
    url = f"{TELEGRAM_API}/bot{bot_token}/sendDocument"
    payload: dict[str, Any] = {"chat_id": chat_id, "document": document_url}
    if caption:
        payload["caption"] = caption[:1024]
        payload["parse_mode"] = parse_mode
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)
    if client is None:
        async with httpx.AsyncClient(**telegram_http_kwargs(60.0)) as c:
            return await _post(c, url, payload)
    return await _post(client, url, payload)


async def send_document_by_bytes(
    bot_token: str,
    chat_id: str | int,
    file_bytes: bytes,
    filename: str = "document.bin",
    caption: str | None = None,
    parse_mode: str = PARSE_MODE_HTML,
    *,
    reply_markup: dict[str, Any] | None = None,
    client: httpx.AsyncClient | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    """Отправить документ как файл (multipart)."""
    api_url = f"{TELEGRAM_API}/bot{bot_token}/sendDocument"
    data: dict[str, Any] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption[:1024]
        data["parse_mode"] = parse_mode
    if reply_markup is not None:
        data["reply_markup"] = json.dumps(reply_markup)
    files = {"document": (filename, file_bytes, "application/octet-stream")}
    return await _post_multipart(client, api_url, data, files, timeout=60.0)


def _error_description(data: dict[str, Any]) -> str:
    """Текст ошибки из ответа Telegram API для показа пользователю."""
    desc = data.get("description") or data.get("error") or ""
    code = data.get("error_code")
    if code is not None and desc:
        return f"{desc} (код {code})"
    return desc or "неизвестная ошибка"


async def _post(client: httpx.AsyncClient, url: str, json: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    """
    Возвращает (data, None) при успехе или (None, error_message) при ошибке.
    """
    try:
        r = await client.post(url, json=json)
        data = r.json() if r.content else {}
        if not r.is_success:
            msg = _error_description(data)
            logger.warning("Telegram API error: %s %s", r.status_code, data)
            return None, msg
        return data, None
    except Exception as e:
        logger.exception("Telegram send failed: %s", e)
        return None, str(e)


async def _post_multipart(
    client: httpx.AsyncClient | None,
    url: str,
    data: dict[str, Any],
    files: dict[str, tuple[str, bytes, str]],
    timeout: float = 30.0,
) -> tuple[dict[str, Any] | None, str | None]:
    """POST multipart/form-data. Возвращает (data, None) при успехе или (None, error_message)."""
    try:
        if client is None:
            async with httpx.AsyncClient(**telegram_http_kwargs(timeout)) as c:
                r = await c.post(url, data=data, files=files)
        else:
            r = await client.post(url, data=data, files=files)
        result = r.json() if r.content else {}
        if not r.is_success:
            msg = _error_description(result)
            logger.warning("Telegram API multipart error: %s %s", r.status_code, result)
            return None, msg
        return result, None
    except Exception as e:
        logger.exception("Telegram multipart send failed: %s", e)
        return None, str(e)
