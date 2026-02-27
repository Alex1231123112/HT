from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage
from admin.api.services import analytics_csv
from database.models import AdminUser, Delivery, Mailing, MailingStat, MailingStatus, News, Promotion, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/users", response_model=GenericMessage)
async def analytics_users(db: AsyncSession = Depends(get_db), admin: AdminUser = Depends(get_current_admin)) -> GenericMessage:
    _ = admin
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    by_type = {
        "total": await db.scalar(select(func.count(User.id))) or 0,
        "horeca": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0,
        "retail": await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0,
        "new_month": await db.scalar(select(func.count(User.id)).where(User.registered_at >= month_ago)) or 0,
        "active": await db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0,
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
    opened = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.opened_at.is_not(None))) or 0
    clicked = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.clicked_at.is_not(None))) or 0
    delivered = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.sent_at.is_not(None))) or 0
    open_rate = round((opened / delivered) * 100, 2) if delivered else 0
    ctr = round((clicked / delivered) * 100, 2) if delivered else 0
    return GenericMessage(
        message="ok",
        data={"total": total, "sent": sent, "delivered": delivered, "opened": opened, "clicked": clicked, "open_rate": open_rate, "ctr": ctr},
    )


@router.get("/content", response_model=GenericMessage)
async def analytics_content(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    promo_active = await db.scalar(select(func.count(Promotion.id)).where(Promotion.is_active.is_(True))) or 0
    news_active = await db.scalar(select(func.count(News.id)).where(News.is_active.is_(True))) or 0
    deliveries_active = await db.scalar(select(func.count(Delivery.id)).where(Delivery.is_active.is_(True))) or 0
    return GenericMessage(
        message="ok",
        data={
            "promotions": await db.scalar(select(func.count(Promotion.id))) or 0,
            "news": await db.scalar(select(func.count(News.id))) or 0,
            "deliveries": await db.scalar(select(func.count(Delivery.id))) or 0,
            "promotions_active": promo_active,
            "news_active": news_active,
            "deliveries_active": deliveries_active,
        },
    )


@router.get("/cohort", response_model=GenericMessage)
async def analytics_cohort(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    users = list((await db.scalars(select(User).where(User.registered_at.is_not(None)))).all())
    grouped: dict[str, int] = defaultdict(int)
    for user in users:
        key = user.registered_at.strftime("%Y-%m")
        grouped[key] += 1
    rows = [{"cohort": key, "users": value} for key, value in sorted(grouped.items())]
    return GenericMessage(message="ok", data={"rows": rows})


@router.get("/conversions", response_model=GenericMessage)
async def analytics_conversions(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    delivered = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.sent_at.is_not(None))) or 0
    clicked = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.clicked_at.is_not(None))) or 0
    conversion = round((clicked / delivered) * 100, 2) if delivered else 0
    return GenericMessage(message="ok", data={"delivered": delivered, "clicked": clicked, "conversion_rate": conversion})


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
        "mailing_messages_sent": await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.sent_at.is_not(None))) or 0,
        "mailing_messages_opened": await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.opened_at.is_not(None)))
        or 0,
        "mailing_messages_clicked": await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.clicked_at.is_not(None)))
        or 0,
        "content_active": (
            (await db.scalar(select(func.count(Promotion.id)).where(Promotion.is_active.is_(True))) or 0)
            + (await db.scalar(select(func.count(News.id)).where(News.is_active.is_(True))) or 0)
            + (await db.scalar(select(func.count(Delivery.id)).where(Delivery.is_active.is_(True))) or 0)
        ),
    }
    return StreamingResponse(iter([analytics_csv(rows)]), media_type="text/csv")
