import logging
import re
from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from bot.keyboards import (
    edit_profile_keyboard,
    menu_keyboard,
    profile_keyboard,
    remove_keyboard,
    request_phone_keyboard,
)
from database.models import User, UserType
from database.session import SessionLocal

router = Router()
logger = logging.getLogger(__name__)

MIN_AGE = 18
BIRTH_DATE_PATTERN = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")


class ProfileEdit(StatesGroup):
    editing_establishment = State()
    editing_full_name = State()
    editing_birth_date = State()
    editing_position = State()
    editing_phone = State()


def _parse_birth_date(text: str) -> date | None:
    m = BIRTH_DATE_PATTERN.match((text or "").strip())
    if not m:
        return None
    try:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= d <= 31 and 1 <= mo <= 12 and 1900 <= y <= date.today().year:
            return date(y, mo, d)
    except (ValueError, TypeError):
        pass
    return None


def _age_years(birth: date) -> int:
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _format_profile(user: User) -> str:
    phone = user.phone_number or "—"
    ut = "HoReCa" if user.user_type == UserType.HORECA else "Retail"
    establishment = user.establishment or "—"
    full_name = user.full_name or "—"
    birth_str = user.birth_date.strftime("%d.%m.%Y") if user.birth_date else "—"
    position = user.position or "—"
    reg = user.registered_at.strftime("%d.%m.%Y") if user.registered_at else "—"
    return (
        "👤 <b>ВАШ ПРОФИЛЬ</b>\n\n"
        f"Телефон: {phone}\n"
        f"Направление: {ut}\n"
        f"Заведение: {establishment}\n"
        f"Имя: {full_name}\n"
        f"Дата рождения: {birth_str}\n"
        f"Должность: {position}\n\n"
        f"Вы зарегистрированы: {reg}"
    )


@router.callback_query(F.data == "menu_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        async with SessionLocal() as session:
            user = await session.get(User, callback.from_user.id)
            if not user or user.deleted_at is not None:
                await callback.message.answer("Сначала выполните регистрацию через /start")
                await callback.answer()
                return
            text = _format_profile(user)
    except SQLAlchemyError:
        logger.exception("Database error loading profile")
        await callback.message.answer("Не удалось загрузить профиль. Попробуйте позже.")
        await callback.answer()
        return
    await callback.message.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "profile_edit")
async def profile_edit_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Что вы хотите изменить?", reply_markup=edit_profile_keyboard())
    await callback.answer()


@router.callback_query(F.data == "edit_establishment")
async def edit_establishment_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileEdit.editing_establishment)
    await callback.message.answer("Введите новое название заведения:")
    await callback.answer()


@router.callback_query(F.data == "edit_full_name")
async def edit_full_name_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileEdit.editing_full_name)
    await callback.message.answer("Введите имя (ФИО или как обращаться):")
    await callback.answer()


@router.callback_query(F.data == "edit_birth_date")
async def edit_birth_date_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileEdit.editing_birth_date)
    await callback.message.answer("Введите дату рождения (ДД.ММ.ГГГГ). Возраст должен быть 18+:")
    await callback.answer()


@router.callback_query(F.data == "edit_position")
async def edit_position_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileEdit.editing_position)
    await callback.message.answer("Введите должность или род деятельности:")
    await callback.answer()


@router.callback_query(F.data == "edit_phone")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ProfileEdit.editing_phone)
    await callback.message.answer("Нажмите кнопку для отправки номера телефона:", reply_markup=request_phone_keyboard())
    await callback.answer()


async def _save_and_show_profile(message: Message, state: FSMContext) -> None:
    await state.clear()
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if not user or user.deleted_at is not None:
                await message.answer("Профиль не найден.")
                return
            text = _format_profile(user)
    except SQLAlchemyError:
        logger.exception("Database error loading profile")
        await message.answer("Не удалось обновить профиль.")
        return
    await message.answer(text, reply_markup=profile_keyboard(), parse_mode="HTML")


@router.message(ProfileEdit.editing_establishment)
async def save_establishment(message: Message, state: FSMContext) -> None:
    val = (message.text or "").strip()
    if len(val) < 2:
        await message.answer("Название заведения слишком короткое. Введите минимум 2 символа.")
        return
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                user.establishment = val
                user.last_activity = datetime.utcnow()
                user.deleted_at = None
                session.add(user)
                await session.commit()
    except SQLAlchemyError:
        logger.exception("Database error updating establishment")
        await message.answer("Не удалось сохранить. Попробуйте позже.")
        await state.clear()
        return
    await _save_and_show_profile(message, state)


@router.message(ProfileEdit.editing_full_name)
async def save_full_name(message: Message, state: FSMContext) -> None:
    val = (message.text or "").strip()
    if len(val) < 2:
        await message.answer("Введите минимум 2 символа.")
        return
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                user.full_name = val
                user.last_activity = datetime.utcnow()
                user.deleted_at = None
                session.add(user)
                await session.commit()
    except SQLAlchemyError:
        logger.exception("Database error updating full_name")
        await message.answer("Не удалось сохранить. Попробуйте позже.")
        await state.clear()
        return
    await _save_and_show_profile(message, state)


@router.message(ProfileEdit.editing_birth_date)
async def save_birth_date(message: Message, state: FSMContext) -> None:
    birth = _parse_birth_date(message.text or "")
    if birth is None:
        await message.answer("❌ Неверный формат. Введите дату в формате ДД.ММ.ГГГГ")
        return
    if _age_years(birth) < MIN_AGE:
        await message.answer("Возраст должен быть 18+. Введите корректную дату.")
        return
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                user.birth_date = birth
                user.last_activity = datetime.utcnow()
                user.deleted_at = None
                session.add(user)
                await session.commit()
    except SQLAlchemyError:
        logger.exception("Database error updating birth_date")
        await message.answer("Не удалось сохранить. Попробуйте позже.")
        await state.clear()
        return
    await _save_and_show_profile(message, state)


@router.message(ProfileEdit.editing_position)
async def save_position(message: Message, state: FSMContext) -> None:
    val = (message.text or "").strip()
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                user.position = val or None
                user.last_activity = datetime.utcnow()
                user.deleted_at = None
                session.add(user)
                await session.commit()
    except SQLAlchemyError:
        logger.exception("Database error updating position")
        await message.answer("Не удалось сохранить. Попробуйте позже.")
        await state.clear()
        return
    await _save_and_show_profile(message, state)


@router.message(ProfileEdit.editing_phone, F.contact)
async def save_phone(message: Message, state: FSMContext) -> None:
    phone = (message.contact.phone_number or "").strip() if message.contact else ""
    if not phone:
        await message.answer("Не удалось получить номер. Нажмите кнопку «Отправить номер телефона».", reply_markup=request_phone_keyboard())
        return
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user:
                user.phone_number = phone
                user.last_activity = datetime.utcnow()
                user.deleted_at = None
                session.add(user)
                await session.commit()
    except SQLAlchemyError:
        logger.exception("Database error updating phone")
        await message.answer("Не удалось сохранить. Попробуйте позже.")
        await state.clear()
        return
    await message.answer("Номер обновлён.", reply_markup=remove_keyboard())
    await _save_and_show_profile(message, state)


@router.message(ProfileEdit.editing_phone)
async def editing_phone_not_contact(message: Message) -> None:
    await message.answer("Пожалуйста, нажмите кнопку «📱 Отправить номер телефона».", reply_markup=request_phone_keyboard())
