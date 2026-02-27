from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import AdminCreate, AdminOut, AdminUpdate, GenericMessage
from admin.api.security import hash_password
from database.models import ActivityLog, AdminUser
from database.session import get_db

router = APIRouter(prefix="/api/admins", tags=["admins"])


@router.get("", response_model=GenericMessage)
async def list_admins(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> GenericMessage:
    _ = admin
    items = list((await db.scalars(select(AdminUser).order_by(AdminUser.created_at.desc()))).all())
    return GenericMessage(message="ok", data={"items": [AdminOut.model_validate(item).model_dump() for item in items]})


@router.get("/{admin_id}", response_model=AdminOut)
async def get_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> AdminOut:
    _ = admin
    item = await db.get(AdminUser, admin_id)
    if not item:
        raise HTTPException(status_code=404, detail="Admin not found")
    return item


@router.post("", response_model=AdminOut, dependencies=[Depends(verify_csrf)])
async def create_admin(
    payload: AdminCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> AdminOut:
    existing = await db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
    if existing:
        raise HTTPException(status_code=409, detail="Admin username already exists")
    if payload.email:
        existing_email = await db.scalar(select(AdminUser).where(AdminUser.email == payload.email.lower()))
        if existing_email:
            raise HTTPException(status_code=409, detail="Admin email already exists")
    item = AdminUser(
        username=payload.username,
        email=payload.email.lower() if payload.email else None,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(item)
    await db.flush()
    db.add(ActivityLog(admin_id=admin.id, action="create_admin", details=f"admin_id={item.id}"))
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/{admin_id}", response_model=AdminOut, dependencies=[Depends(verify_csrf)])
async def update_admin(
    admin_id: int,
    payload: AdminUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> AdminOut:
    item = await db.get(AdminUser, admin_id)
    if not item:
        raise HTTPException(status_code=404, detail="Admin not found")
    if payload.email is not None:
        if payload.email:
            normalized = payload.email.lower()
            existing_email = await db.scalar(select(AdminUser).where(AdminUser.email == normalized, AdminUser.id != admin_id))
            if existing_email:
                raise HTTPException(status_code=409, detail="Admin email already exists")
            item.email = normalized
        else:
            item.email = None
    if payload.role is not None:
        item.role = payload.role
    if payload.is_active is not None:
        item.is_active = payload.is_active
    if payload.password:
        item.password_hash = hash_password(payload.password)
    db.add(item)
    db.add(ActivityLog(admin_id=admin.id, action="update_admin", details=f"admin_id={admin_id}"))
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/{admin_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_admin(
    admin_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> GenericMessage:
    item = await db.get(AdminUser, admin_id)
    if not item:
        raise HTTPException(status_code=404, detail="Admin not found")
    if item.username == admin.username:
        raise HTTPException(status_code=400, detail="Cannot delete current admin")
    await db.delete(item)
    db.add(ActivityLog(admin_id=admin.id, action="delete_admin", details=f"admin_id={admin_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
