from aiogram import Router
from aiogram.types import Message

from bot.keyboards import menu_keyboard
from database.models import User
from database.session import SessionLocal

router = Router()


@router.message()
async def fallback_message(message: Message) -> None:
    establishment = None
    if message.from_user:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                establishment = user.establishment
    kb = await menu_keyboard(user_establishment=establishment)
    await message.answer(
        "Не понял сообщение. Используйте <code>/help</code> или <code>/menu</code>, либо нажмите <code>/start</code> для регистрации.",
        reply_markup=kb,
        parse_mode="HTML",
    )
