import logging
import re
from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import SQLAlchemyError

from bot.keyboards import (
    birth_date_retry_keyboard,
    menu_keyboard,
    remove_keyboard,
    request_phone_keyboard,
    type_keyboard,
)
from config.settings import get_settings
from database.models import User, UserType
from database.session import SessionLocal

router = Router()
settings = get_settings()
logger = logging.getLogger(__name__)

MIN_AGE = 18
BIRTH_DATE_PATTERN = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")


class Registration(StatesGroup):
    waiting_phone = State()
    choosing_type = State()
    waiting_establishment = State()
    waiting_full_name = State()
    waiting_birth_date = State()
    waiting_position = State()


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


def _format_phone(phone: str | None) -> str:
    if not phone:
        return ""
    return phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user is not None and user.deleted_at is None:
                await state.clear()
                await message.answer(
                    "С возвращением! Выберите раздел:",
                    reply_markup=menu_keyboard(with_update_profile=True),
                    parse_mode="HTML",
                )
                return
    except SQLAlchemyError:
        logger.exception("Database error in start")
    await state.set_state(Registration.waiting_phone)
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Мы — поставщики табака для кальяна в Казани.\n\n"
        "Возможности бота:\n"
        "• Актуальные акции для вашего типа заведения\n"
        "• Новинки табаков\n"
        "• Информация о приходах\n"
        "• Связь с менеджерами\n"
        "• Информация о мероприятиях\n\n"
        "Для продолжения регистрации нам нужен ваш номер телефона.\n"
        "Нажмите кнопку ниже",
        reply_markup=request_phone_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "start_reregister")
async def start_reregister(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.waiting_phone)
    await callback.message.answer(
        "Обновление профиля. Для продолжения нужен ваш номер телефона.\nНажмите кнопку ниже.",
        reply_markup=request_phone_keyboard(),
    )
    await callback.answer()


@router.message(Registration.waiting_phone, F.contact)
async def receive_phone(message: Message, state: FSMContext) -> None:
    contact = message.contact
    phone = (contact.phone_number or "").strip()
    if not phone:
        await message.answer("Не удалось получить номер. Нажмите кнопку «Отправить номер телефона».", reply_markup=request_phone_keyboard())
        return
    await state.update_data(phone_number=phone)
    await state.set_state(Registration.choosing_type)
    await message.answer(
        f"✅ Номер получен!\n{phone}\n\nТеперь выберите ваше направление:",
        reply_markup=remove_keyboard(),
    )
    await message.answer("Выберите ваше направление:", reply_markup=type_keyboard())


@router.message(Registration.waiting_phone)
async def waiting_phone_not_contact(message: Message) -> None:
    await message.answer("Пожалуйста, нажмите кнопку «📱 Отправить номер телефона» для продолжения.", reply_markup=request_phone_keyboard())


@router.callback_query(Registration.choosing_type, F.data.startswith("type_"))
async def choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    selected = callback.data.split("_", maxsplit=1)[1]
    if selected not in {"horeca", "retail"}:
        await callback.message.answer("Некорректный выбор типа. Нажмите /start и повторите.")
        await callback.answer()
        return
    await state.update_data(user_type=selected)
    await state.set_state(Registration.waiting_establishment)
    if selected == "horeca":
        text = (
            "Введите название вашего заведения:\n"
            "(например: «Кальянная Lounge», «Ресторан Восток», «Бар Спорт»)"
        )
    else:
        text = (
            "Введите название вашего заведения:\n"
            "(например: «Табачная лавка №1», «Магазин Кальянный Мир», «Торговая точка на Баумана»)"
        )
    await callback.message.answer(text)
    await callback.answer()


@router.message(Registration.waiting_establishment)
async def save_establishment(message: Message, state: FSMContext) -> None:
    establishment = (message.text or "").strip()
    if len(establishment) < 2:
        await message.answer("Название заведения слишком короткое. Введите минимум 2 символа.")
        return
    await state.update_data(establishment=establishment)
    await state.set_state(Registration.waiting_full_name)
    await message.answer("Как вас зовут?\n(ФИО или как к вам обращаться)")


@router.message(Registration.waiting_full_name)
async def save_full_name(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if len(full_name) < 2:
        await message.answer("Введите имя (минимум 2 символа).")
        return
    await state.update_data(full_name=full_name)
    await state.set_state(Registration.waiting_birth_date)
    await message.answer(
        "Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):\nНапример: 25.01.1993"
    )


@router.callback_query(F.data == "birth_date_retry")
async def birth_date_retry(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.waiting_birth_date)
    await callback.message.answer(
        "Введите вашу дату рождения (в формате ДД.ММ.ГГГГ):\nНапример: 25.01.1993"
    )
    await callback.answer()


@router.message(Registration.waiting_birth_date)
async def save_birth_date(message: Message, state: FSMContext) -> None:
    birth = _parse_birth_date(message.text or "")
    if birth is None:
        await message.answer("❌ Неверный формат. Введите дату в формате ДД.ММ.ГГГГ")
        return
    age = _age_years(birth)
    if age < MIN_AGE:
        await message.answer(
            "⚠️ <b>ВНИМАНИЕ</b>\n\n"
            "К сожалению, наш сервис предназначен только для лиц старше 18 лет.\n\n"
            "Если вы ошиблись при вводе даты, попробуйте снова:",
            reply_markup=birth_date_retry_keyboard(),
            parse_mode="HTML",
        )
        return
    await state.update_data(birth_date=birth)
    await state.set_state(Registration.waiting_position)
    await message.answer(
        "Кем вы работаете?\n(Должность или род деятельности)\n\n"
        "Например:\n• Администратор кальянной\n• Управляющий рестораном\n• Владелец табачного магазина\n• Бариста/кальянщик"
    )


@router.message(Registration.waiting_position)
async def save_position_and_finish(message: Message, state: FSMContext) -> None:
    position = (message.text or "").strip() or "—"
    data = await state.get_data()
    user_type = UserType.HORECA if data["user_type"] == "horeca" else UserType.RETAIL
    user_type_label = "HoReCa" if user_type == UserType.HORECA else "Retail"
    phone = data.get("phone_number") or ""
    establishment = data["establishment"]
    full_name = data.get("full_name") or ""
    birth_date: date | None = data.get("birth_date")

    try:
        async with SessionLocal() as session:
            user = await session.get(User, message.from_user.id)
            if user is None:
                user = User(
                    id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    phone_number=phone,
                    full_name=full_name or None,
                    birth_date=birth_date,
                    position=position if position != "—" else None,
                    user_type=user_type,
                    establishment=establishment,
                    registered_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                )
            else:
                user.username = message.from_user.username
                user.first_name = message.from_user.first_name
                user.last_name = message.from_user.last_name
                user.phone_number = phone
                user.full_name = full_name or None
                user.birth_date = birth_date
                user.position = position if position != "—" else None
                user.user_type = user_type
                user.establishment = establishment
                user.last_activity = datetime.utcnow()
                user.deleted_at = None  # повторная регистрация = снять пометку удаления
            session.add(user)
            await session.commit()
            logger.info("User registered in DB: id=%s, establishment=%s", message.from_user.id, establishment)
    except SQLAlchemyError:
        logger.exception("Database error during registration")
        await message.answer("Сервис временно недоступен. Попробуйте снова через 1–2 минуты.")
        return

    await state.clear()
    birth_str = birth_date.strftime("%d.%m.%Y") if birth_date else "—"
    confirm = (
        "✅ <b>РЕГИСТРАЦИЯ ЗАВЕРШЕНА!</b>\n\n"
        "Ваши данные:\n\n"
        f"📞 Телефон: {phone}\n"
        f"🏢 Направление: {user_type_label}\n"
        f"🏨 Заведение: {establishment}\n"
        f"👤 Имя: {full_name}\n"
        f"🎂 Дата рождения: {birth_str}\n"
        f"💼 Должность: {position}\n\n"
        "Теперь вы будете получать:\n"
        "• Акции для вашего сегмента\n"
        "• Новинки табаков\n"
        "• Информацию о приходах\n"
        "• Анонсы мероприятий\n\n"
        "Добро пожаловать в семью! 👋"
    )
    await message.answer(confirm, parse_mode="HTML")
    await message.answer("Выберите раздел:", reply_markup=menu_keyboard(with_update_profile=True))
