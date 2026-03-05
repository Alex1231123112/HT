from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy import func, select

from bot.keyboards import events_back_keyboard, menu_keyboard
from bot.utils import render_content, render_events
from config.settings import get_settings
from database.models import Delivery, Event, EventRegistration, Manager, News, Promotion, User
from database.session import SessionLocal

router = Router()

HELP_TEXT = (
    "<b>Доступные команды:</b>\n"
    "/start — регистрация или обновление профиля\n"
    "/help — справка\n"
    "/menu — показать главное меню\n\n"
    "После регистрации: <b>Акции</b>, <b>Новинки</b>, <b>Приходы</b>, <b>Мероприятия</b>, <b>Мой профиль</b>, связь с менеджером."
)


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")


@router.message(Command("menu"))
async def menu_command(message: Message) -> None:
    establishment = None
    if message.from_user:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                establishment = user.establishment
    kb = await menu_keyboard(user_establishment=establishment)
    await message.answer("<b>Главное меню:</b>", reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "menu_promotions")
async def promotions(callback: CallbackQuery) -> None:
    if callback.message:
        await render_content(
            callback.message, Promotion, "🎁 Актуальные акции:", user_id=callback.from_user.id
        )
    await callback.answer()


@router.callback_query(F.data == "menu_news")
async def news(callback: CallbackQuery) -> None:
    if callback.message:
        await render_content(
            callback.message, News, "📰 Актуальные новинки:", user_id=callback.from_user.id
        )
    await callback.answer()


@router.callback_query(F.data == "menu_deliveries")
async def deliveries(callback: CallbackQuery) -> None:
    if callback.message:
        await render_content(
            callback.message, Delivery, "📦 Актуальные приходы:", user_id=callback.from_user.id
        )
    await callback.answer()


@router.callback_query(F.data == "menu_events")
async def events(callback: CallbackQuery) -> None:
    if callback.message:
        await render_events(callback.message, user_id=callback.from_user.id)
        await callback.message.answer("Выберите раздел:", reply_markup=events_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu_back")
async def menu_back(callback: CallbackQuery) -> None:
    establishment = None
    if callback.from_user:
        async with SessionLocal() as session:
            user = await session.get(User, callback.from_user.id)
            if user:
                establishment = user.establishment
    kb = await menu_keyboard(with_update_profile=True, user_establishment=establishment)
    await callback.message.answer("📱 <b>Главное меню</b>\n\nВыберите раздел:", reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("manager_"))
async def manager_contact(callback: CallbackQuery) -> None:
    """При нажатии на менеджера — выводит сообщение с контактами и кнопкой «Написать»."""
    data = callback.data
    if not callback.message:
        await callback.answer()
        return
    settings = get_settings()
    if data == "manager_default":
        uname = (settings.manager_username or "manager").strip().lstrip("@")
        if not uname:
            await callback.answer("Менеджер не настроен.", show_alert=True)
            return
        text = "💬 <b>Связь с менеджером</b>\n\nНажмите кнопку ниже, чтобы написать в Telegram."
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Написать в Telegram", url=f"https://t.me/{uname}")],
            ]
        )
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await callback.answer()
        return
    try:
        manager_id = int(data.removeprefix("manager_"))
    except ValueError:
        await callback.answer()
        return
    async with SessionLocal() as session:
        manager = await session.get(Manager, manager_id)
        if not manager or not manager.is_active:
            await callback.answer("Менеджер не найден.", show_alert=True)
            return
        uname = (manager.telegram_username or "").strip().lstrip("@")
        if not uname:
            await callback.answer("У менеджера не указан Telegram.", show_alert=True)
            return
        name = manager.full_name or "Менеджер"
        phone = manager.phone_number or ""
        establishment = manager.establishment or ""
        lines = [f"💬 <b>{name}</b>"]
        if establishment:
            lines.append(f"🏢 {establishment}")
        if phone:
            lines.append(f"📞 {phone}")
        lines.append(f"\n@{uname}")
        lines.append("\nНажмите кнопку ниже, чтобы написать в Telegram.")
        text = "\n".join(lines)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✉️ Написать в Telegram", url=f"https://t.me/{uname}")],
            ]
        )
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("event_reg_"))
async def event_register(callback: CallbackQuery) -> None:
    try:
        event_id = int(callback.data.removeprefix("event_reg_"))
    except ValueError:
        await callback.answer("Ошибка", show_alert=True)
        return
    user_id = callback.from_user.id if callback.from_user else 0
    if not user_id:
        await callback.answer("Ошибка", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        if not user or user.deleted_at:
            await callback.answer("Сначала завершите регистрацию в боте.", show_alert=True)
            return
        event = await session.get(Event, event_id)
        if not event or not event.is_active:
            await callback.answer("Мероприятие не найдено или уже завершено.", show_alert=True)
            return
        existing = await session.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user_id,
            )
        )
        if existing:
            await callback.answer("Вы уже записаны.")
            return
        if event.max_places is not None:
            cnt = await session.scalar(
                select(func.count())
                .select_from(EventRegistration)
                .where(EventRegistration.event_id == event_id)
            )
            if (cnt or 0) >= event.max_places:
                await callback.answer("К сожалению, мест больше нет.", show_alert=True)
                return
        session.add(EventRegistration(event_id=event_id, user_id=user_id))
        await session.commit()
    await callback.answer("✅ Вы записаны на мероприятие!")


@router.callback_query(F.data.startswith("event_unreg_"))
async def event_unregister(callback: CallbackQuery) -> None:
    try:
        event_id = int(callback.data.removeprefix("event_unreg_"))
    except ValueError:
        await callback.answer("Ошибка", show_alert=True)
        return
    user_id = callback.from_user.id if callback.from_user else 0
    if not user_id:
        await callback.answer("Ошибка", show_alert=True)
        return
    async with SessionLocal() as session:
        reg = await session.scalar(
            select(EventRegistration).where(
                EventRegistration.event_id == event_id,
                EventRegistration.user_id == user_id,
            )
        )
        if reg:
            await session.delete(reg)
            await session.commit()
    await callback.answer("Запись на мероприятие отменена.")
