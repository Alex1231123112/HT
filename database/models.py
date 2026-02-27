from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


def enum_values(enum_cls: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_cls]


class UserType(StrEnum):
    HORECA = "horeca"
    RETAIL = "retail"
    ALL = "all"


class MailingTarget(StrEnum):
    ALL = "all"
    HORECA = "horeca"
    RETAIL = "retail"
    CUSTOM = "custom"


class MailingStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"


class MediaType(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"
    NONE = "none"


class AdminRole(StrEnum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="user_type", values_callable=enum_values))
    establishment: Mapped[str] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="promo_user_type", values_callable=enum_values))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="news_user_type", values_callable=enum_values))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="delivery_user_type", values_callable=enum_values))
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Mailing(Base):
    __tablename__ = "mailings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="mailing_media_type", values_callable=enum_values), default=MediaType.NONE
    )
    target_type: Mapped[MailingTarget] = mapped_column(
        Enum(MailingTarget, name="mailing_target_type", values_callable=enum_values)
    )
    custom_targets: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[MailingStatus] = mapped_column(
        Enum(MailingStatus, name="mailing_status", values_callable=enum_values), default=MailingStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    send_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    stats: Mapped[list["MailingStat"]] = relationship(back_populates="mailing")


class MailingStat(Base):
    __tablename__ = "mailing_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mailing_id: Mapped[int] = mapped_column(ForeignKey("mailings.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    mailing: Mapped[Mailing] = relationship(back_populates="stats")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[AdminRole] = mapped_column(Enum(AdminRole, name="admin_role", values_callable=enum_values))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
