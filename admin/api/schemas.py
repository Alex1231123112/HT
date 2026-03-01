from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from database.models import (
    AdminRole,
    ContentPlanContentType,
    ContentPlanStatus,
    DistributionChannelType,
    MailingStatus,
    MailingTarget,
    MediaType,
    UserType,
)


class LoginRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    identifier: str | None = None
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    full_name: str | None = None
    birth_date: date | None = None
    position: str | None = None
    user_type: UserType
    establishment: str
    is_active: bool = True


class UserCreate(UserBase):
    id: int


class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    full_name: str | None = None
    birth_date: date | None = None
    position: str | None = None
    user_type: UserType | None = None
    establishment: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    id: int
    registered_at: datetime
    last_activity: datetime | None
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class ContentBase(BaseModel):
    title: str
    description: str = ""
    image_url: str | None = None
    user_type: UserType
    published_at: datetime | None = None
    is_active: bool = True


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    user_type: UserType | None = None
    published_at: datetime | None = None
    is_active: bool | None = None


class ContentOut(ContentBase):
    id: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    title: str
    description: str = ""
    image_url: str | None = None
    user_type: UserType
    event_date: datetime
    location: str = ""
    is_active: bool = True
    max_places: int | None = None  # None = без лимита мест


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    user_type: UserType | None = None
    event_date: datetime | None = None
    location: str | None = None
    is_active: bool | None = None
    max_places: int | None = None


class EventOut(EventBase):
    id: int
    created_at: datetime
    registered_count: int = 0  # заполняется в роутере

    class Config:
        from_attributes = True


class EventRegistrationOut(BaseModel):
    id: int
    event_id: int
    user_id: int
    registered_at: datetime
    user_username: str | None = None
    user_full_name: str | None = None
    user_phone: str | None = None
    user_establishment: str | None = None

    class Config:
        from_attributes = True


class MailingCreate(BaseModel):
    text: str
    media_url: str | None = None
    media_type: MediaType = MediaType.NONE
    target_type: MailingTarget
    custom_targets: list[int] | None = None
    scheduled_at: datetime | None = None
    speed: str | None = "medium"


class MailingUpdate(BaseModel):
    text: str | None = None
    media_url: str | None = None
    media_type: MediaType | None = None
    target_type: MailingTarget | None = None
    custom_targets: list[int] | None = None
    scheduled_at: datetime | None = None
    status: MailingStatus | None = None


class MailingOut(BaseModel):
    id: int
    text: str
    media_url: str | None
    media_type: MediaType
    target_type: MailingTarget
    custom_targets: list[int] | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    status: MailingStatus
    created_at: datetime
    send_attempts: int = 0
    last_error: str | None = None
    cancelled_at: datetime | None = None

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total: int
    horeca: int
    retail: int
    active_content: int
    total_mailings: int
    new_today: int = 0
    new_week: int = 0
    new_month: int = 0
    mailings_month: int = 0
    active_promotions: int = 0
    active_news: int = 0
    active_deliveries: int = 0


class UserStatsOut(BaseModel):
    total: int
    active: int
    horeca: int
    retail: int


class EstablishmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    user_type: UserType


class EstablishmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    user_type: UserType | None = None


class EstablishmentOut(BaseModel):
    id: int
    name: str
    user_type: str  # "horeca" | "retail" | "all"
    user_count: int = 0  # кол-во пользователей с этим заведением (по полю establishment)
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class SettingItem(BaseModel):
    key: str
    value: str


class SettingBatch(BaseModel):
    items: list[SettingItem]


class GenericMessage(BaseModel):
    message: str
    data: dict[str, Any] | None = None


class AdminCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    email: str | None = None
    password: str = Field(min_length=8, max_length=128)
    role: AdminRole = AdminRole.MANAGER


class AdminUpdate(BaseModel):
    email: str | None = None
    role: AdminRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AdminOut(BaseModel):
    id: int
    username: str
    email: str | None = None
    role: AdminRole
    is_active: bool
    created_at: datetime
    last_login: datetime | None = None

    class Config:
        from_attributes = True


# --- Каналы рассылки ---


class DistributionChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    channel_type: DistributionChannelType
    telegram_ref: str | None = None
    is_active: bool = True


class DistributionChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    telegram_ref: str | None = None
    is_active: bool | None = None


class DistributionChannelOut(BaseModel):
    id: int
    name: str
    channel_type: DistributionChannelType
    telegram_ref: str | None = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Контент план ---


class ContentPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content_type: ContentPlanContentType
    content_id: int | None = None
    custom_title: str | None = None
    custom_description: str | None = None
    custom_media_url: str | None = None
    scheduled_at: datetime | None = None
    channel_ids: list[int] = Field(default_factory=list)


class ContentPlanUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content_type: ContentPlanContentType | None = None
    content_id: int | None = None
    custom_title: str | None = None
    custom_description: str | None = None
    custom_media_url: str | None = None
    scheduled_at: datetime | None = None
    status: ContentPlanStatus | None = None
    channel_ids: list[int] | None = None


class ContentPlanOut(BaseModel):
    id: int
    title: str
    content_type: ContentPlanContentType
    content_id: int | None = None
    custom_title: str | None = None
    custom_description: str | None = None
    custom_media_url: str | None = None
    scheduled_at: datetime | None = None
    status: ContentPlanStatus
    sent_at: datetime | None = None
    created_at: datetime
    channel_ids: list[int] = Field(default_factory=list)

    class Config:
        from_attributes = True
