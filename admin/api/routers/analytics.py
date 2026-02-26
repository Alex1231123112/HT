from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage
from admin.api.services import analytics_csv
from database.models import AdminUser, Delivery, Mailing, MailingStatus, News, Promotion, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/users", response_model=GenericMessage)
async def analytics_users(db: AsyncSession = Depends(get_db), admin: AdminUser = Depends(get_current_admin)) -> GenericMessage:
    _ = admin
    by_type = {
        "horeca": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0,
        "retail": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0,
    }
    return GenericMessage(message="ok", data=by_type)


@router.get("/mailings", response_model=GenericMessage)
async def analytics_mailings(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    total = await db.scalar(select(func.count(Mailing.id))) or 0
    sent = await db.scalar(select(func.count(Mailing.id)).where(Mailing.status == MailingStatus.SENT)) or 0
    return GenericMessage(message="ok", data={"total": total, "sent": sent})


@router.get("/content", response_model=GenericMessage)
async def analytics_content(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    return GenericMessage(
        message="ok",
        data={
            "promotions": await db.scalar(select(func.count(Promotion.id))) or 0,
            "news": await db.scalar(select(func.count(News.id))) or 0,
            "deliveries": await db.scalar(select(func.count(Delivery.id))) or 0,
        },
    )


@router.get("/export")
async def analytics_export(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> StreamingResponse:
    _ = admin
    rows = {
        "users_total": await db.scalar(select(func.count(User.id))) or 0,
        "users_horeca": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0,
        "users_retail": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0,
        "mailings_total": await db.scalar(select(func.count(Mailing.id))) or 0,
        "mailings_sent": await db.scalar(select(func.count(Mailing.id)).where(Mailing.status == MailingStatus.SENT)) or 0,
    }
    return StreamingResponse(iter([analytics_csv(rows)]), media_type="text/csv")
