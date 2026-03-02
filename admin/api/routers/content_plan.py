import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.content_plan_sender import send_plan_to_telegram
from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import (
    ContentPlanCreate,
    ContentPlanItemOut,
    ContentPlanOut,
    ContentPlanUpdate,
    GenericMessage,
)
from config.settings import get_settings
from database.models import (
    ActivityLog,
    AdminUser,
    ContentPlan,
    ContentPlanChannel,
    ContentPlanItem,
    ContentPlanStatus,
    DistributionChannel,
)
from database.session import get_db

router = APIRouter(prefix="/api/content-plan", tags=["content_plan"])
logger = logging.getLogger(__name__)


async def _plan_to_out(db: AsyncSession, plan: ContentPlan) -> ContentPlanOut:
    """Добавить channel_ids и items к плану."""
    ch_rows = (
        await db.execute(
            select(ContentPlanChannel.channel_id).where(ContentPlanChannel.plan_id == plan.id)
        )
    ).scalars().all()
    channel_ids = list(ch_rows)
    item_list = (
        await db.execute(
            select(ContentPlanItem).where(ContentPlanItem.plan_id == plan.id).order_by(ContentPlanItem.sort_order)
        )
    ).scalars().all()
    items = [ContentPlanItemOut.model_validate(row) for row in item_list]
    data = {
        "id": plan.id,
        "title": plan.title,
        "content_type": plan.content_type,
        "content_id": plan.content_id,
        "custom_title": plan.custom_title,
        "custom_description": plan.custom_description,
        "custom_media_url": plan.custom_media_url,
        "scheduled_at": plan.scheduled_at,
        "status": plan.status,
        "sent_at": plan.sent_at,
        "created_at": plan.created_at,
        "channel_ids": channel_ids,
        "items": items,
    }
    return ContentPlanOut(**data)


@router.get("", response_model=list[ContentPlanOut])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[ContentPlanOut]:
    _ = admin
    result = await db.scalars(select(ContentPlan).order_by(ContentPlan.created_at.desc()))
    plans = list(result.all())
    return [await _plan_to_out(db, p) for p in plans]


@router.get("/{plan_id}", response_model=ContentPlanOut)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentPlanOut:
    _ = admin
    plan = await db.get(ContentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return await _plan_to_out(db, plan)


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Привести datetime к naive UTC для совместимости с PostgreSQL/asyncpg."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.post("", response_model=ContentPlanOut, dependencies=[Depends(verify_csrf)])
async def create_plan(
    payload: ContentPlanCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin", "manager")),
) -> ContentPlanOut:
    channel_ids = payload.channel_ids or []
    items_data = getattr(payload, "items", None) or []
    data = payload.model_dump(exclude={"channel_ids", "items"})
    if data.get("scheduled_at") is not None:
        data["scheduled_at"] = _naive_utc(data["scheduled_at"])
    plan = ContentPlan(**data)
    db.add(plan)
    try:
        await db.flush()
        for cid in channel_ids:
            db.add(ContentPlanChannel(plan_id=plan.id, channel_id=cid))
        for i, it in enumerate(items_data):
            db.add(
                ContentPlanItem(
                    plan_id=plan.id,
                    sort_order=i,
                    content_type=it.content_type,
                    content_id=it.content_id,
                    custom_title=it.custom_title,
                    custom_description=it.custom_description,
                    custom_media_url=it.custom_media_url,
                )
            )
        db.add(ActivityLog(admin_id=admin.id, action="create_content_plan", details=f"plan={plan.title}"))
        await db.commit()
        await db.refresh(plan)
        return await _plan_to_out(db, plan)
    except IntegrityError as e:
        await db.rollback()
        logger.warning("Content plan create IntegrityError: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Ошибка данных: проверьте, что выбранные каналы существуют и не удалены.",
        ) from e
    except Exception as e:
        await db.rollback()
        logger.exception("Content plan create failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{plan_id}", response_model=ContentPlanOut, dependencies=[Depends(verify_csrf)])
async def update_plan(
    plan_id: int,
    payload: ContentPlanUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentPlanOut:
    plan = await db.get(ContentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    data = payload.model_dump(exclude_unset=True, exclude={"channel_ids", "items"})
    for k, v in data.items():
        setattr(plan, k, v)
    if payload.channel_ids is not None:
        await db.execute(delete(ContentPlanChannel).where(ContentPlanChannel.plan_id == plan_id))
        for cid in payload.channel_ids:
            db.add(ContentPlanChannel(plan_id=plan_id, channel_id=cid))
    if payload.items is not None:
        await db.execute(delete(ContentPlanItem).where(ContentPlanItem.plan_id == plan_id))
        for i, it in enumerate(payload.items):
            db.add(
                ContentPlanItem(
                    plan_id=plan_id,
                    sort_order=i,
                    content_type=it.content_type,
                    content_id=it.content_id,
                    custom_title=it.custom_title,
                    custom_description=it.custom_description,
                    custom_media_url=it.custom_media_url,
                )
            )
    db.add(plan)
    db.add(ActivityLog(admin_id=admin.id, action="update_content_plan", details=f"plan_id={plan_id}"))
    await db.commit()
    await db.refresh(plan)
    return await _plan_to_out(db, plan)


@router.post("/{plan_id}/send", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def send_plan_now(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin", "manager")),
) -> GenericMessage:
    """Отправить запись контент-плана в привязанные каналы (бот и/или Telegram-канал). Для тестов и ручного запуска."""
    plan = await db.get(ContentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if plan.status == ContentPlanStatus.SENT:
        raise HTTPException(status_code=400, detail="Plan already sent")
    settings = get_settings()
    if not (settings.bot_token or "").strip():
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN не задан в .env. Укажите токен бота для отправки в Telegram.",
        )
    result = await send_plan_to_telegram(db, plan, settings.bot_token)
    plan.status = ContentPlanStatus.SENT
    plan.sent_at = datetime.utcnow()
    db.add(plan)
    db.add(ActivityLog(admin_id=admin.id, action="send_content_plan", details=f"plan_id={plan_id}"))
    await db.commit()
    total = result["sent_bot"] + result["sent_channel"]
    channels_count = result.get("channels_count", 0)
    hint = None
    if total == 0:
        if channels_count == 0:
            hint = (
                "К плану не привязаны активные каналы. Откройте план на редактирование, "
                "выберите «Каналы рассылки» (хотя бы один) и сохраните. Для публикации в канал нужен канал типа "
                "«Telegram-канал» с указанным @username канала; бот должен быть администратором канала."
            )
        else:
            hint = (
                "Ни одно сообщение не доставлено (привязано каналов: %s). Проверьте: для «Бот» — в базе есть "
                "пользователи; для Telegram-канала — бот добавлен в канал как администратор с правом публикации "
                "и в настройках канала указан верный @channel (или chat_id). См. ошибки ниже."
            ) % channels_count
        logger.warning("Content plan %s send: 0 messages. channels_count=%s", plan_id, channels_count)
    return GenericMessage(
        message="sent",
        data={
            "sent_bot": result["sent_bot"],
            "sent_channel": result["sent_channel"],
            "errors": result["errors"],
            "hint": hint,
            "channels_count": channels_count,
        },
    )


@router.delete("/{plan_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    plan = await db.get(ContentPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(plan)
    db.add(ActivityLog(admin_id=admin.id, action="delete_content_plan", details=f"plan_id={plan_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
