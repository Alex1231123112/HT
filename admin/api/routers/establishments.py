from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import (
    EstablishmentCreate,
    EstablishmentOut,
    EstablishmentUpdate,
    GenericMessage,
)
from database.models import ActivityLog, AdminUser, Establishment, User
from database.session import get_db

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/establishments", tags=["establishments"])


async def _establishment_to_out(db: AsyncSession, est: Establishment) -> EstablishmentOut:
    """Добавить user_count (сколько пользователей указали это заведение)."""
    cnt = await db.scalar(
        select(func.count(User.id)).where(
            User.establishment == est.name,
            User.deleted_at.is_(None),
        )
    )
    return EstablishmentOut(
        id=est.id,
        name=est.name,
        user_type=getattr(est.user_type, "value", str(est.user_type)),
        user_count=cnt or 0,
        created_at=est.created_at,
    )


@router.get("", response_model=list[EstablishmentOut])
async def list_establishments(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> list[EstablishmentOut]:
    _ = admin
    result = await db.execute(
        select(Establishment).order_by(Establishment.user_type, Establishment.name)
    )
    items = list(result.scalars().all())
    return [await _establishment_to_out(db, e) for e in items]


@router.get("/{establishment_id}", response_model=EstablishmentOut)
async def get_establishment(
    establishment_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> EstablishmentOut:
    _ = admin
    est = await db.get(Establishment, establishment_id)
    if not est:
        raise HTTPException(status_code=404, detail="Establishment not found")
    return await _establishment_to_out(db, est)


@router.post("", response_model=EstablishmentOut, dependencies=[Depends(verify_csrf)])
async def create_establishment(
    payload: EstablishmentCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> EstablishmentOut:
    est = Establishment(name=payload.name, user_type=payload.user_type)
    db.add(est)
    db.add(ActivityLog(admin_id=admin.id, action="create_establishment", details=f"name={est.name}"))
    await db.commit()
    await db.refresh(est)
    return await _establishment_to_out(db, est)


@router.put("/{establishment_id}", response_model=EstablishmentOut, dependencies=[Depends(verify_csrf)])
async def update_establishment(
    establishment_id: int,
    payload: EstablishmentUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> EstablishmentOut:
    est = await db.get(Establishment, establishment_id)
    if not est:
        raise HTTPException(status_code=404, detail="Establishment not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(est, k, v)
    db.add(est)
    db.add(ActivityLog(admin_id=admin.id, action="update_establishment", details=f"id={establishment_id}"))
    await db.commit()
    await db.refresh(est)
    return await _establishment_to_out(db, est)


@router.delete("/{establishment_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_establishment(
    establishment_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    est = await db.get(Establishment, establishment_id)
    if not est:
        raise HTTPException(status_code=404, detail="Establishment not found")
    await db.delete(est)
    db.add(ActivityLog(admin_id=admin.id, action="delete_establishment", details=f"id={establishment_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
