from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from database.models import AdminRole, MailingStatus, MailingTarget, MediaType, UserType


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
    user_type: UserType
    establishment: str
    is_active: bool = True


class UserCreate(UserBase):
    id: int


class UserUpdate(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    user_type: UserType | None = None
    establishment: str | None = None
    is_active: bool | None = None


class UserOut(UserBase):
    id: int
    registered_at: datetime
    last_activity: datetime | None

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
