from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage, StatsOut
from admin.api.services import content_count
from database.models import ActivityLog, AdminUser, Mailing, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=StatsOut)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> StatsOut:
    _ = admin
    total = await db.scalar(select(func.count(User.id))) or 0
    horeca = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0
    retail = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0
    active_content = await content_count(db)
    total_mailings = await db.scalar(select(func.count(Mailing.id))) or 0
    return StatsOut(
        total=total,
        horeca=horeca,
        retail=retail,
        active_content=active_content,
        total_mailings=total_mailings,
    )


@router.get("/users-chart", response_model=GenericMessage)
async def users_chart(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    return GenericMessage(
        message="ok",
        data={
            "horeca": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0,
            "retail": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0,
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
        data={"items": [{"action": r.action, "created_at": r.created_at.isoformat()} for r in rows]},
    )
