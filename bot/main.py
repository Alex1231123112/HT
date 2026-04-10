import asyncio
import logging
import os
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from bot.handlers import setup_handlers
from config.logging import configure_logging
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
configure_logging()
settings = get_settings()
_logger = logging.getLogger(__name__)


def _redact_db_url(url: str) -> str:
    if "@" in url:
        return url.split("@", 1)[-1]
    return url.replace("sqlite", "sqlite***")


def _redact_proxy_url(url: str) -> str:
    try:
        u = urlparse(url)
        if u.username is not None:
            host = u.hostname or ""
            port = f":{u.port}" if u.port else ""
            return f"{u.scheme}://***@{host}{port}{u.path or ''}"
    except Exception:
        pass
    return "***"


def _telegram_proxy_url() -> str | None:
    if settings.telegram_proxy and settings.telegram_proxy.strip():
        return settings.telegram_proxy.strip()
    for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
        v = os.environ.get(key)
        if v and v.strip():
            return v.strip()
    return None


async def main() -> None:
    _logger.info("Bot DB: %s", _redact_db_url(settings.database_url))
    proxy = _telegram_proxy_url()
    if proxy:
        _logger.info("Telegram API proxy: %s", _redact_proxy_url(proxy))
        bot = Bot(token=settings.bot_token, session=AiohttpSession(proxy=proxy))
    else:
        bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(setup_handlers())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
