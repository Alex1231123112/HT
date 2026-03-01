from datetime import datetime
from io import StringIO

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import (
    Delivery,
    Mailing,
    MailingStat,
    MailingStatus,
    MailingTarget,
    News,
    Promotion,
    User,
    UserType,
)


async def list_content(model, db: AsyncSession, user_type: UserType | None):
    query = select(model).order_by(model.created_at.desc())
    if user_type:
        query = query.where(or_(model.user_type == user_type, model.user_type == UserType.ALL))
    return list((await db.scalars(query)).all())


async def get_content_by_id(model, item_id: int, db: AsyncSession):
    item = await db.get(model, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


def _normalize_content_payload(payload: dict) -> dict:
    """Приводит payload к типам, ожидаемым ORM (user_type — enum, published_at — datetime | None)."""
    from datetime import datetime as dt

    out = dict(payload)
    if "user_type" in out and isinstance(out["user_type"], str):
        out["user_type"] = UserType(out["user_type"])
    if "published_at" in out and out["published_at"] is not None and isinstance(out["published_at"], str):
        try:
            out["published_at"] = dt.fromisoformat(out["published_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            out["published_at"] = None
    return out


async def create_content(model, payload: dict, db: AsyncSession):
    data = _normalize_content_payload(payload)
    # Только атрибуты, которые есть у модели (без id — автоинкремент)
    allowed = set(model.__table__.c.keys()) - {"id"}
    data = {k: v for k, v in data.items() if k in allowed}
    item = model(**data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_content(model, item_id: int, payload: dict, db: AsyncSession):
    item = await get_content_by_id(model, item_id, db)
    for key, value in payload.items():
        setattr(item, key, value)
    item.updated_at = datetime.utcnow()
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def delete_content(model, item_id: int, db: AsyncSession):
    item = await get_content_by_id(model, item_id, db)
    await db.delete(item)
    await db.commit()


def matches_target(user: User, mailing: Mailing) -> bool:
    if mailing.target_type == MailingTarget.ALL:
        return True
    if mailing.target_type == MailingTarget.HORECA:
        return user.user_type == UserType.HORECA
    if mailing.target_type == MailingTarget.RETAIL:
        return user.user_type == UserType.RETAIL
    return bool(mailing.custom_targets and user.id in mailing.custom_targets)


async def dispatch_mailing(db: AsyncSession, mailing: Mailing) -> int:
    try:
        users = list((await db.scalars(select(User).where(User.is_active.is_(True)))).all())
        recipients = [u for u in users if matches_target(u, mailing)]
        now = datetime.utcnow()
        for recipient in recipients:
            db.add(MailingStat(mailing_id=mailing.id, user_id=recipient.id, sent_at=now))
        mailing.status = MailingStatus.SENT
        mailing.sent_at = now
        mailing.last_error = None
        mailing.send_attempts += 1
        db.add(mailing)
        await db.commit()
        return len(recipients)
    except Exception as exc:
        mailing.send_attempts += 1
        mailing.last_error = str(exc)
        db.add(mailing)
        await db.commit()
        raise


async def content_count(db: AsyncSession) -> int:
    return (
        (await db.scalar(select(func.count(Promotion.id)).where(Promotion.is_active.is_(True))) or 0)
        + (await db.scalar(select(func.count(News.id)).where(News.is_active.is_(True))) or 0)
        + (await db.scalar(select(func.count(Delivery.id)).where(Delivery.is_active.is_(True))) or 0)
    )


def _csv_escape(s: str | None) -> str:
    if not s:
        return ""
    s = str(s).replace('"', '""')
    return f'"{s}"' if "," in s or "\n" in s or '"' in s else s


def users_csv(users: list[User]) -> str:
    buff = StringIO()
    buff.write(
        "id,username,first_name,last_name,phone_number,full_name,birth_date,position,"
        "user_type,establishment,registered_at,last_activity,is_active,deleted_at\n"
    )
    for user in users:
        registered_at = user.registered_at.isoformat() if user.registered_at else ""
        last_activity = user.last_activity.isoformat() if user.last_activity else ""
        deleted_at = user.deleted_at.isoformat() if user.deleted_at else ""
        birth_date = user.birth_date.isoformat() if user.birth_date else ""
        buff.write(
            f"{user.id},{_csv_escape(user.username)},{_csv_escape(user.first_name)},{_csv_escape(user.last_name)},"
            f"{_csv_escape(user.phone_number)},{_csv_escape(user.full_name)},{birth_date},{_csv_escape(user.position)},"
            f"{user.user_type.value},{_csv_escape(user.establishment)},{registered_at},{last_activity},"
            f"{user.is_active},{deleted_at}\n"
        )
    return buff.getvalue()


def logs_csv(log_rows: list[dict]) -> str:
    buff = StringIO()
    buff.write("id,admin_id,action,details,created_at\n")
    for row in log_rows:
        buff.write(
            f"{row['id']},{row.get('admin_id') or ''},{row['action']},{row['details'] or ''},{row['created_at']}\n"
        )
    return buff.getvalue()


def analytics_csv(rows: dict[str, int]) -> str:
    buff = StringIO()
    buff.write("metric,value\n")
    for key, value in rows.items():
        buff.write(f"{key},{value}\n")
    return buff.getvalue()


def list_bot_content_for_user_query(model, user: User):
    return select(model).where(
        and_(model.is_active.is_(True), or_(model.user_type == user.user_type, model.user_type == UserType.ALL))
    )
