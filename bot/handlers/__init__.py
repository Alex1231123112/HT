from aiogram import Router

from bot.handlers.content import router as content_router
from bot.handlers.fallback import router as fallback_router
from bot.handlers.profile import router as profile_router
from bot.handlers.registration import router as registration_router


def setup_handlers() -> Router:
    root = Router()
    root.include_router(registration_router)
    root.include_router(content_router)
    root.include_router(profile_router)
    root.include_router(fallback_router)
    return root
