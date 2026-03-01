import asyncio
import logging

from aiogram import Bot, Dispatcher

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


async def main() -> None:
    _logger.info("Bot DB: %s", _redact_db_url(settings.database_url))
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(setup_handlers())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
