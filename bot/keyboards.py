from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from config.settings import get_settings
from database.models import Manager
from database.session import SessionLocal

settings = get_settings()


def type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏨 HoReCa (кальяные, рестораны, бары)", callback_data="type_horeca")],
            [InlineKeyboardButton(text="🏪 Retail (магазины, табачные лавки)", callback_data="type_retail")],
        ]
    )


async def _get_manager_button(user_establishment: str | None) -> list[list[InlineKeyboardButton]]:
    """
    Всегда одна кнопка «Менеджер». При нажатии показывается список (один или все менеджеры).
    """
    async with SessionLocal() as session:
        result = await session.execute(
            select(Manager).where(Manager.is_active.is_(True), Manager.telegram_username.isnot(None))
        )
        managers = list(result.scalars().all())
    if not managers:
        uname = (settings.manager_username or "manager").strip()
        if uname and not uname.startswith("replace-"):
            return [[InlineKeyboardButton(text="💬 Менеджер", callback_data="menu_manager")]]
        return []
    return [[InlineKeyboardButton(text="💬 Менеджер", callback_data="menu_manager")]]


async def menu_keyboard(
    with_update_profile: bool = False,
    user_establishment: str | None = None,
) -> InlineKeyboardMarkup:
    manager_rows = await _get_manager_button(user_establishment)
    rows = [
        [
            InlineKeyboardButton(text="🎁 Акции", callback_data="menu_promotions"),
            InlineKeyboardButton(text="📰 Новинки", callback_data="menu_news"),
        ],
        [
            InlineKeyboardButton(text="📦 Приходы", callback_data="menu_deliveries"),
            InlineKeyboardButton(text="🎪 Мероприятия", callback_data="menu_events"),
        ],
        *manager_rows,
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile")],
    ]
    if with_update_profile:
        rows.insert(0, [InlineKeyboardButton(text="🔄 Обновить профиль", callback_data="start_reregister")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="profile_edit")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_back")],
        ]
    )


def edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Название заведения", callback_data="edit_establishment")],
            [InlineKeyboardButton(text="👤 Имя", callback_data="edit_full_name")],
            [InlineKeyboardButton(text="🎂 Дату рождения", callback_data="edit_birth_date")],
            [InlineKeyboardButton(text="💼 Должность", callback_data="edit_position")],
            [InlineKeyboardButton(text="📱 Телефон", callback_data="edit_phone")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_profile")],
        ]
    )


def events_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎁 Акции", callback_data="menu_promotions"),
                InlineKeyboardButton(text="📰 Новинки", callback_data="menu_news"),
            ],
            [
                InlineKeyboardButton(text="📦 Приходы", callback_data="menu_deliveries"),
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_back"),
            ],
        ]
    )


def birth_date_retry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Ввести дату рождения заново", callback_data="birth_date_retry")],
        ]
    )
