from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage, StatsOut
from admin.api.services import content_count
from database.models import ActivityLog, AdminUser, Delivery, Mailing, News, Promotion, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=StatsOut)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> StatsOut:
    _ = admin
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    total = await db.scalar(select(func.count(User.id))) or 0
    horeca = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0
    retail = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0
    active_content = await content_count(db)
    total_mailings = await db.scalar(select(func.count(Mailing.id))) or 0
    new_today = await db.scalar(select(func.count(User.id)).where(User.registered_at >= day_ago)) or 0
    new_week = await db.scalar(select(func.count(User.id)).where(User.registered_at >= week_ago)) or 0
    new_month = await db.scalar(select(func.count(User.id)).where(User.registered_at >= month_ago)) or 0
    mailings_month = await db.scalar(select(func.count(Mailing.id)).where(Mailing.created_at >= month_ago)) or 0
    active_promotions = await db.scalar(select(func.count(Promotion.id)).where(Promotion.is_active.is_(True))) or 0
    active_news = await db.scalar(select(func.count(News.id)).where(News.is_active.is_(True))) or 0
    active_deliveries = await db.scalar(select(func.count(Delivery.id)).where(Delivery.is_active.is_(True))) or 0
    return StatsOut(
        total=total,
        horeca=horeca,
        retail=retail,
        active_content=active_content,
        total_mailings=total_mailings,
        new_today=new_today,
        new_week=new_week,
        new_month=new_month,
        mailings_month=mailings_month,
        active_promotions=active_promotions,
        active_news=active_news,
        active_deliveries=active_deliveries,
    )


@router.get("/users-chart", response_model=GenericMessage)
async def users_chart(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    today = datetime.utcnow().date()
    points: list[dict[str, int | str]] = []
    for offset in range(13, -1, -1):
        day = today - timedelta(days=offset)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        count = await db.scalar(
            select(func.count(User.id)).where(User.registered_at >= day_start, User.registered_at < day_end)
        ) or 0
        points.append({"date": day.isoformat(), "count": count})
    return GenericMessage(
        message="ok",
        data={
            "horeca": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0,
            "retail": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0,
            "daily_growth": points,
        },
    )


@router.get("/activity", response_model=GenericMessage)
async def last_activity(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    rows = list((await db.scalars(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(20))).all())
    return GenericMessage(
        message="ok",
        data={
            "items": [
                {
                    "action": r.action,
                    "details": r.details,
                    "admin_id": r.admin_id,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
        },
    )
