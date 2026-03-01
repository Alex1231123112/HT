from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from config.settings import get_settings

settings = get_settings()


def request_phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove(remove_keyboard=True)


def type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏨 HoReCa (кальяные, рестораны, бары)", callback_data="type_horeca")],
            [InlineKeyboardButton(text="🏪 Retail (магазины, табачные лавки)", callback_data="type_retail")],
        ]
    )


def menu_keyboard(with_update_profile: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="🎁 Акции", callback_data="menu_promotions"),
            InlineKeyboardButton(text="📰 Новинки", callback_data="menu_news"),
        ],
        [
            InlineKeyboardButton(text="📦 Приходы", callback_data="menu_deliveries"),
            InlineKeyboardButton(text="🎪 Мероприятия", callback_data="menu_events"),
        ],
        [
            InlineKeyboardButton(text="💬 Менеджер", url=f"https://t.me/{settings.manager_username}"),
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="menu_profile"),
        ],
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
