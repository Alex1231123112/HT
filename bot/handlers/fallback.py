from aiogram import Router
from aiogram.types import Message

from bot.keyboards import menu_keyboard

router = Router()


@router.message()
async def fallback_message(message: Message) -> None:
    await message.answer(
        "Не понял сообщение. Используйте <code>/help</code> или <code>/menu</code>, либо нажмите <code>/start</code> для регистрации.",
        reply_markup=menu_keyboard(),
        parse_mode="HTML",
    )
