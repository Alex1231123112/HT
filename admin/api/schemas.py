from datetime import datetime
from typing import Any

from pydantic import BaseModel

from database.models import MailingStatus, MailingTarget, MediaType, UserType


class LoginRequest(BaseModel):
    username: str
    password: str


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
