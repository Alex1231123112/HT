import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from config.logging import configure_logging
from config.settings import get_settings
from database.models import Delivery, News, Promotion, User, UserType
from database.session import SessionLocal

logging.basicConfig(level=logging.INFO)
configure_logging()
router = Router()
settings = get_settings()


class Registration(StatesGroup):
    choosing_type = State()
    waiting_establishment = State()


def type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="HoReCa", callback_data="type_horeca")],
            [InlineKeyboardButton(text="Retail", callback_data="type_retail")],
        ]
    )


def menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Акции", callback_data="menu_promotions")],
            [InlineKeyboardButton(text="📰 Новинки", callback_data="menu_news")],
            [InlineKeyboardButton(text="📦 Приходы", callback_data="menu_deliveries")],
            [InlineKeyboardButton(text="💬 Написать менеджеру", url=f"https://t.me/{settings.manager_username}")],
        ]
    )


HELP_TEXT = (
    "Доступные команды:\n"
    "/start - регистрация или обновление профиля\n"
    "/help - справка\n"
    "/menu - показать главное меню\n\n"
    "После регистрации используйте кнопки: Акции, Новинки, Приходы или связь с менеджером."
)


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    await state.set_state(Registration.choosing_type)
    await message.answer(
        "Привет! Я бот с новостями и акциями.\nВыберите направление:",
        reply_markup=type_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=menu_keyboard())


@router.callback_query(Registration.choosing_type, F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    selected = callback.data.split("_", maxsplit=1)[1]
    if selected not in {"horeca", "retail"}:
        await callback.message.answer("Некорректный выбор типа. Нажмите /start и повторите.")
        await callback.answer()
        return
    await state.update_data(user_type=selected)
    await state.set_state(Registration.waiting_establishment)
    await callback.message.answer("Укажите название вашего заведения:")
    await callback.answer()


@router.message(Registration.waiting_establishment)
async def save_registration(message: Message, state: FSMContext) -> None:
    establishment = (message.text or "").strip()
    if len(establishment) < 2:
        await message.answer("Название заведения слишком короткое. Введите минимум 2 символа.")
        return
    data = await state.get_data()
    user_type = UserType.HORECA if data["user_type"] == "horeca" else UserType.RETAIL
    user_type_label = "HoReCa" if user_type == UserType.HORECA else "Retail"
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user is None:
                user = User(
                    id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    user_type=user_type,
                    establishment=establishment,
                    registered_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                )
            else:
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.user_type = user_type
                user.establishment = establishment
                user.last_activity = datetime.utcnow()
            session.add(user)
            await session.commit()
    except SQLAlchemyError:
        logging.exception("Database error during registration")
        await message.answer("Сервис временно недоступен. Попробуйте снова через 1-2 минуты.")
        return
    await state.clear()
    await message.answer(
        f"✅ Регистрация завершена!\nТеперь вы будете получать актуальную информацию для {user_type_label}.",
        reply_markup=menu_keyboard(),
    )


async def _render_content(message: Message, model, title: str) -> None:
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if not user:
                await message.answer("Сначала выполните регистрацию через /start")
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
    except SQLAlchemyError:
        logging.exception("Database error while loading content")
        await message.answer("Не удалось получить данные. Попробуйте позже.")
        return
    if not items:
        await message.answer(f"{title}\nПока нет актуальных записей.")
        return
    lines = [title]
    for item in items[:5]:
        lines.append(f"\n• {item.title}\n{item.description}")
        if item.image_url:
            lines.append(f"Изображение: {item.image_url}")
    await message.answer("\n".join(lines))


@router.callback_query(F.data == "menu_promotions")
async def promotions(callback: CallbackQuery) -> None:
    await _render_content(callback.message, Promotion, "🎁 Актуальные акции:")
    await callback.answer()


@router.callback_query(F.data == "menu_news")
async def news(callback: CallbackQuery) -> None:
    await _render_content(callback.message, News, "📰 Актуальные новинки:")
    await callback.answer()


@router.callback_query(F.data == "menu_deliveries")
async def deliveries(callback: CallbackQuery) -> None:
    await _render_content(callback.message, Delivery, "📦 Актуальные приходы:")
    await callback.answer()


@router.message()
async def fallback_message(message: Message) -> None:
    await message.answer(
        "Не понял сообщение. Используйте /help или /menu, либо нажмите /start для регистрации.",
        reply_markup=menu_keyboard(),
    )


async def main() -> None:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
