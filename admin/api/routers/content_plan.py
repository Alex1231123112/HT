from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import (
    ContentPlanCreate,
    ContentPlanOut,
    ContentPlanUpdate,
    GenericMessage,
)
from database.models import ActivityLog, AdminUser, ContentPlan, ContentPlanChannel, DistributionChannel
from database.session import get_db

router = APIRouter(prefix="/api/content-plan", tags=["content_plan"])


async def _plan_to_out(db: AsyncSession, plan: ContentPlan) -> ContentPlanOut:
    """Добавить channel_ids к плану."""
    rows = (
        await db.execute(
            select(ContentPlanChannel.channel_id).where(ContentPlanChannel.plan_id == plan.id)
        )
    ).scalars().all()
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
        "channel_ids": list(rows),
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


@router.post("", response_model=ContentPlanOut, dependencies=[Depends(verify_csrf)])
async def create_plan(
    payload: ContentPlanCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin", "manager")),
) -> ContentPlanOut:
    channel_ids = payload.channel_ids or []
    data = payload.model_dump(exclude={"channel_ids"})
    plan = ContentPlan(**data)
    db.add(plan)
    await db.flush()
    for cid in channel_ids:
        db.add(ContentPlanChannel(plan_id=plan.id, channel_id=cid))
    db.add(ActivityLog(admin_id=admin.id, action="create_content_plan", details=f"plan={plan.title}"))
    await db.commit()
    await db.refresh(plan)
    return await _plan_to_out(db, plan)


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
    data = payload.model_dump(exclude_unset=True, exclude={"channel_ids"})
    for k, v in data.items():
        setattr(plan, k, v)
    if payload.channel_ids is not None:
        await db.execute(delete(ContentPlanChannel).where(ContentPlanChannel.plan_id == plan_id))
        for cid in payload.channel_ids:
            db.add(ContentPlanChannel(plan_id=plan_id, channel_id=cid))
    db.add(plan)
    db.add(ActivityLog(admin_id=admin.id, action="update_content_plan", details=f"plan_id={plan_id}"))
    await db.commit()
    await db.refresh(plan)
    return await _plan_to_out(db, plan)


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
