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


async def create_content(model, payload: dict, db: AsyncSession):
    item = model(**payload)
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


def users_csv(users: list[User]) -> str:
    buff = StringIO()
    buff.write("id,username,user_type,establishment,registered_at\n")
    for user in users:
        registered_at = user.registered_at.isoformat() if user.registered_at else ""
        buff.write(
            f"{user.id},{user.username or ''},{user.user_type.value},"
            f"{user.establishment},{registered_at}\n"
        )
    return buff.getvalue()


def logs_csv(log_rows: list[dict]) -> str:
    buff = StringIO()
    buff.write("id,action,details,created_at\n")
    for row in log_rows:
        buff.write(f"{row['id']},{row['action']},{row['details'] or ''},{row['created_at']}\n")
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
