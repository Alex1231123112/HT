from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from config.settings import get_settings

settings = get_settings()

# Тексты кнопок (должны совпадать с проверкой в хендлерах)
BTN_PROMOTIONS = "🎁 Акции"
BTN_NEWS = "📰 Новинки"
BTN_DELIVERIES = "📦 Приходы"
BTN_EVENTS = "🎪 Мероприятия"
BTN_MANAGER = "💬 Менеджер"
BTN_PROFILE = "👤 Мой профиль"
BTN_MENU = "🏠 Главное меню"
BTN_UPDATE_PROFILE = "🔄 Обновить профиль"
BTN_EDIT_PROFILE = "✏️ Редактировать профиль"
BTN_EDIT_ESTABLISHMENT = "🏢 Название заведения"
BTN_EDIT_FULL_NAME = "👤 Имя"
BTN_EDIT_BIRTH_DATE = "🎂 Дату рождения"
BTN_EDIT_POSITION = "💼 Должность"
BTN_EDIT_PHONE = "📱 Телефон"
BTN_BACK = "◀️ Назад"
BTN_TYPE_HORECA = "🏨 HoReCa (кальяные, рестораны, бары)"
BTN_TYPE_RETAIL = "🏪 Retail (магазины, табачные лавки)"
BTN_BIRTH_RETRY = "🔄 Ввести дату рождения заново"


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove(remove_keyboard=True)


remove_reply_keyboard = remove_keyboard  # alias for backward compatibility


def request_phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def type_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TYPE_HORECA)],
            [KeyboardButton(text=BTN_TYPE_RETAIL)],
        ],
        resize_keyboard=True,
    )


async def menu_keyboard(
    with_update_profile: bool = False,
    user_establishment: str | None = None,
) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=BTN_PROMOTIONS), KeyboardButton(text=BTN_NEWS)],
        [KeyboardButton(text=BTN_DELIVERIES), KeyboardButton(text=BTN_EVENTS)],
        [KeyboardButton(text=BTN_MANAGER)],
        [KeyboardButton(text=BTN_PROFILE)],
    ]
    if with_update_profile:
        rows.insert(0, [KeyboardButton(text=BTN_UPDATE_PROFILE)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EDIT_PROFILE)],
            [KeyboardButton(text=BTN_MENU)],
        ],
        resize_keyboard=True,
    )


def edit_profile_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_EDIT_ESTABLISHMENT)],
            [KeyboardButton(text=BTN_EDIT_FULL_NAME)],
            [KeyboardButton(text=BTN_EDIT_BIRTH_DATE)],
            [KeyboardButton(text=BTN_EDIT_POSITION)],
            [KeyboardButton(text=BTN_EDIT_PHONE)],
            [KeyboardButton(text=BTN_BACK)],
        ],
        resize_keyboard=True,
    )


def events_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_PROMOTIONS), KeyboardButton(text=BTN_NEWS)],
            [KeyboardButton(text=BTN_DELIVERIES), KeyboardButton(text=BTN_MENU)],
        ],
        resize_keyboard=True,
    )


def birth_date_retry_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BIRTH_RETRY)]],
        resize_keyboard=True,
    )
