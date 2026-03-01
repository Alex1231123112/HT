from fastapi import APIRouter, Depends, HTTPException

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import (
    DistributionChannelCreate,
    DistributionChannelOut,
    DistributionChannelUpdate,
    GenericMessage,
)
from database.models import ActivityLog, AdminUser, DistributionChannel
from database.session import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("", response_model=list[DistributionChannelOut])
async def list_channels(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[DistributionChannelOut]:
    _ = admin
    result = await db.scalars(select(DistributionChannel).order_by(DistributionChannel.id))
    return list(result.all())


@router.get("/{channel_id}", response_model=DistributionChannelOut)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> DistributionChannelOut:
    _ = admin
    ch = await db.get(DistributionChannel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    return ch


@router.post("", response_model=DistributionChannelOut, dependencies=[Depends(verify_csrf)])
async def create_channel(
    payload: DistributionChannelCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin", "manager")),
) -> DistributionChannelOut:
    ch = DistributionChannel(**payload.model_dump())
    db.add(ch)
    db.add(ActivityLog(admin_id=admin.id, action="create_channel", details=f"channel={ch.name}"))
    await db.commit()
    await db.refresh(ch)
    return ch


@router.put("/{channel_id}", response_model=DistributionChannelOut, dependencies=[Depends(verify_csrf)])
async def update_channel(
    channel_id: int,
    payload: DistributionChannelUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> DistributionChannelOut:
    ch = await db.get(DistributionChannel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(ch, k, v)
    db.add(ch)
    db.add(ActivityLog(admin_id=admin.id, action="update_channel", details=f"channel_id={channel_id}"))
    await db.commit()
    await db.refresh(ch)
    return ch


@router.delete("/{channel_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    ch = await db.get(DistributionChannel, channel_id)
    if not ch:
        raise HTTPException(status_code=404, detail="Channel not found")
    await db.delete(ch)
    db.add(ActivityLog(admin_id=admin.id, action="delete_channel", details=f"channel_id={channel_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
