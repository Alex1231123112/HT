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
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> list[UserOut]:
    _ = admin
    query = select(User).order_by(User.registered_at.desc())
    if user_type:
        query = query.where(User.user_type == user_type)
    if search:
        query = query.where(or_(User.username.ilike(f"%{search}%"), User.establishment.ilike(f"%{search}%")))
    return list((await db.scalars(query)).all())


@router.get("/stats", response_model=UserStatsOut)
async def users_stats(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> UserStatsOut:
    _ = admin
    total = await db.scalar(select(func.count(User.id))) or 0
    active = await db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    horeca = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.HORECA)) or 0
    retail = await db.scalar(select(func.count(User.id)).where(User.user_type == UserType.RETAIL)) or 0
    return UserStatsOut(total=total, active=active, horeca=horeca, retail=retail)


@router.get("/export")
async def export_users(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> StreamingResponse:
    _ = admin
    users = list((await db.scalars(select(User))).all())
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
    if not user:
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
    if not user:
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
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    db.add(ActivityLog(admin_id=admin.id, action="delete_user", details=f"user={user_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
