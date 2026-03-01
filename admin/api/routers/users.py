from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import GenericMessage, UserCreate, UserOut, UserStatsOut, UserUpdate
from admin.api.services import users_csv
from database.models import ActivityLog, AdminUser, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserOut, dependencies=[Depends(verify_csrf)])
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> UserOut:
    user = User(**payload.model_dump())
    db.add(user)
    db.add(ActivityLog(admin_id=admin.id, action="create_user", details=f"user={user.id}"))
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=list[UserOut])
async def list_users(
    user_type: UserType | None = Query(default=None),
    search: str | None = Query(default=None),
    include_deleted: bool = Query(default=False),
    activity_state: str | None = Query(default=None, pattern="^(active|stale|inactive)$"),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> list[UserOut]:
    _ = admin
    query = select(User).order_by(User.registered_at.desc())
    if not include_deleted:
        query = query.where(User.deleted_at.is_(None))
    if user_type:
        query = query.where(User.user_type == user_type)
    if search:
        query = query.where(
            or_(
                User.username.ilike(f"%{search}%"),
                User.establishment.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
                User.phone_number.ilike(f"%{search}%"),
            )
        )
    if activity_state:
        now = datetime.utcnow()
        if activity_state == "active":
            query = query.where(User.is_active.is_(True), User.last_activity >= now - timedelta(days=7))
        elif activity_state == "stale":
            query = query.where(
                User.is_active.is_(True),
                User.last_activity.is_not(None),
                User.last_activity < now - timedelta(days=7),
                User.last_activity >= now - timedelta(days=30),
            )
        elif activity_state == "inactive":
            query = query.where(or_(User.is_active.is_(False), User.last_activity < now - timedelta(days=30)))
    users_list = list((await db.scalars(query)).all())
    import logging
    logging.getLogger("uvicorn.error").info("list_users returning %s users", len(users_list))
    return users_list


@router.get("/count", response_model=GenericMessage)
async def users_count(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    """Диагностика: сколько пользователей видит API (всего в БД, без фильтра deleted)."""
    total = await db.scalar(select(func.count(User.id))) or 0
    return GenericMessage(message="ok", data={"count": total})


@router.get("/stats", response_model=UserStatsOut)
async def users_stats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> UserStatsOut:
    _ = admin
    total = await db.scalar(select(func.count(User.id)).where(User.deleted_at.is_(None))) or 0
    active = await db.scalar(select(func.count(User.id)).where(User.is_active.is_(True), User.deleted_at.is_(None))) or 0
    horeca = (
        await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA, User.deleted_at.is_(None))) or 0
    )
    retail = (
        await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL, User.deleted_at.is_(None))) or 0
    )
    return UserStatsOut(total=total, active=active, horeca=horeca, retail=retail)


@router.get("/export")
async def export_users(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> StreamingResponse:
    _ = admin
    users = list((await db.scalars(select(User).where(User.deleted_at.is_(None)))).all())
    csv_data = users_csv(users)
    return StreamingResponse(iter([csv_data]), media_type="text/csv")


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> UserOut:
    _ = admin
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserOut, dependencies=[Depends(verify_csrf)])
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> UserOut:
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.add(user)
    db.add(ActivityLog(admin_id=admin.id, action="update_user", details=f"user={user_id}"))
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    user = await db.get(User, user_id)
    if not user or user.deleted_at is not None:
        raise HTTPException(status_code=404, detail="User not found")
    user.deleted_at = datetime.utcnow()
    user.is_active = False
    db.add(user)
    db.add(ActivityLog(admin_id=admin.id, action="soft_delete_user", details=f"user={user_id}"))
    await db.commit()
    return GenericMessage(message="deleted")


@router.post("/bulk", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def bulk_users(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    user_ids = [int(item) for item in payload.get("user_ids", []) if str(item).isdigit()]
    operation = str(payload.get("operation", "")).strip()
    if not user_ids:
        raise HTTPException(status_code=422, detail="user_ids are required")
    if operation not in {"activate", "deactivate", "soft_delete", "restore"}:
        raise HTTPException(status_code=422, detail="Unsupported operation")
    users = list((await db.scalars(select(User).where(User.id.in_(user_ids)))).all())
    now = datetime.utcnow()
    changed = 0
    for user in users:
        if operation == "activate":
            user.is_active = True
            if user.deleted_at is not None:
                continue
        elif operation == "deactivate":
            user.is_active = False
        elif operation == "soft_delete":
            user.deleted_at = now
            user.is_active = False
        elif operation == "restore":
            user.deleted_at = None
            user.is_active = True
        db.add(user)
        changed += 1
    db.add(ActivityLog(admin_id=admin.id, action="bulk_users", details=f"op={operation};count={changed}"))
    await db.commit()
    return GenericMessage(message="ok", data={"updated": changed})
