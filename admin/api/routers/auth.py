from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage, LoginRequest, TokenResponse
from admin.api.security import create_access_token, revoke_token, verify_password
from database.models import ActivityLog, AdminUser
from database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()
LOGIN_ATTEMPTS: dict[str, list[datetime]] = {}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    now = datetime.utcnow()
    ip = request.client.host if request.client else "unknown"
    LOGIN_ATTEMPTS[ip] = [t for t in LOGIN_ATTEMPTS.get(ip, []) if now - t < timedelta(minutes=10)]
    if len(LOGIN_ATTEMPTS[ip]) >= 5:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many login attempts")
    LOGIN_ATTEMPTS[ip].append(now)

    admin = await db.scalar(select(AdminUser).where(AdminUser.username == payload.username))
    if not admin or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=admin.username, extra={"role": admin.role.value})
    admin.last_login = now
    db.add(admin)
    db.add(ActivityLog(admin_id=admin.id, action="login", details="Admin login", ip_address=ip))
    await db.commit()
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=GenericMessage)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GenericMessage:
    revoke_token(credentials.credentials)
    db.add(ActivityLog(admin_id=admin.id, action="logout", details="Admin logout"))
    await db.commit()
    return GenericMessage(message="logged_out")


@router.get("/me", response_model=GenericMessage)
async def me(admin: AdminUser = Depends(get_current_admin)) -> GenericMessage:
    return GenericMessage(message="ok", data={"username": admin.username, "role": admin.role.value})
