from fastapi import APIRouter, Depends, HTTPException

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import GenericMessage, ManagerCreate, ManagerOut, ManagerUpdate
from database.models import ActivityLog, AdminUser, Manager
from database.session import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/managers", tags=["managers"])


@router.get("", response_model=list[ManagerOut])
async def list_managers(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> list[ManagerOut]:
    _ = admin
    result = await db.execute(select(Manager).order_by(Manager.created_at.desc()))
    items = list(result.scalars().all())
    return items


@router.get("/{manager_id}", response_model=ManagerOut)
async def get_manager(
    manager_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ManagerOut:
    _ = admin
    item = await db.get(Manager, manager_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager not found")
    return item


@router.post("", response_model=ManagerOut, dependencies=[Depends(verify_csrf)])
async def create_manager(
    payload: ManagerCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> ManagerOut:
    item = Manager(**payload.model_dump())
    db.add(item)
    db.add(ActivityLog(admin_id=admin.id, action="create_manager", details=f"manager_id={item.id}"))
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{manager_id}", response_model=ManagerOut, dependencies=[Depends(verify_csrf)])
async def update_manager(
    manager_id: int,
    payload: ManagerUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ManagerOut:
    item = await db.get(Manager, manager_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.add(item)
    db.add(ActivityLog(admin_id=admin.id, action="update_manager", details=f"manager_id={manager_id}"))
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{manager_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_manager(
    manager_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    item = await db.get(Manager, manager_id)
    if not item:
        raise HTTPException(status_code=404, detail="Manager not found")
    await db.delete(item)
    db.add(ActivityLog(admin_id=admin.id, action="delete_manager", details=f"manager_id={manager_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
