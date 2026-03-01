from datetime import datetime
from enum import StrEnum

from datetime import date
from sqlalchemy import BigInteger, JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
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


class DistributionChannelType(StrEnum):
    BOT = "bot"  # рассылка подписчикам бота
    TELEGRAM_CHANNEL = "telegram_channel"  # Telegram-канал или чат


class ContentPlanStatus(StrEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENT = "sent"
    CANCELLED = "cancelled"


class ContentPlanContentType(StrEnum):
    PROMOTION = "promotion"
    NEWS = "news"
    DELIVERY = "delivery"
    EVENT = "event"
    CUSTOM = "custom"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user id (64-bit)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    position: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="user_type", values_callable=enum_values))
    establishment: Mapped[str] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    event_registrations: Mapped[list["EventRegistration"]] = relationship(
        "EventRegistration", back_populates="user", cascade="all, delete-orphan"
    )


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="promotions_user_type", values_callable=enum_values))
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


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="event_user_type", values_callable=enum_values))
    event_date: Mapped[datetime] = mapped_column(DateTime)
    location: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_places: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = без лимита
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    registrations: Mapped[list["EventRegistration"]] = relationship(
        "EventRegistration", back_populates="event", cascade="all, delete-orphan"
    )


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_event_registration_event_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped["Event"] = relationship(Event, back_populates="registrations")
    user: Mapped["User"] = relationship("User", back_populates="event_registrations")


class Establishment(Base):
    """Справочник заведений (название + тип). Пользователи ссылаются на заведение по названию (поле establishment)."""

    __tablename__ = "establishments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    user_type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="establishment_user_type", values_callable=enum_values)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType, name="deliveries_user_type", values_callable=enum_values))
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


class DistributionChannel(Base):
    """Канал рассылки: бот или Telegram-канал."""

    __tablename__ = "distribution_channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    channel_type: Mapped[DistributionChannelType] = mapped_column(
        Enum(DistributionChannelType, name="distribution_channel_type", values_callable=enum_values)
    )
    telegram_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)  # @username или chat_id для канала
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContentPlan(Base):
    """План публикации контента в бот и каналы."""

    __tablename__ = "content_plan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[ContentPlanContentType] = mapped_column(
        Enum(ContentPlanContentType, name="content_plan_content_type", values_callable=enum_values)
    )
    content_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # id акции/новости/поставки
    custom_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    custom_media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ContentPlanStatus] = mapped_column(
        Enum(ContentPlanStatus, name="content_plan_status", values_callable=enum_values),
        default=ContentPlanStatus.DRAFT,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ContentPlanChannel(Base):
    """Связь плана с каналами (многие ко многим)."""

    __tablename__ = "content_plan_channels"

    plan_id: Mapped[int] = mapped_column(ForeignKey("content_plan.id", ondelete="CASCADE"), primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        ForeignKey("distribution_channels.id", ondelete="CASCADE"), primary_key=True
    )
