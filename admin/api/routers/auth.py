import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin
from admin.api.schemas import GenericMessage, LoginRequest, TokenResponse
from admin.api.security import create_access_token, hash_password, revoke_token, verify_password
from config.settings import get_settings
from database.models import ActivityLog, AdminUser
from database.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)
LOGIN_ATTEMPTS: dict[str, list[datetime]] = {}
PASSWORD_RESET_TOKENS: dict[str, tuple[str, datetime]] = {}


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    settings = get_settings()
    now = datetime.utcnow()
    ip = request.client.host if request.client else "unknown"
    window = timedelta(minutes=settings.login_rate_limit_window_minutes)
    identifier = (payload.identifier or payload.username or payload.email or "").strip()
    if not identifier:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Identifier is required")
    lock_key = f"{ip}:{identifier.lower()}"
    LOGIN_ATTEMPTS[lock_key] = [t for t in LOGIN_ATTEMPTS.get(lock_key, []) if now - t < window]
    if len(LOGIN_ATTEMPTS[lock_key]) >= settings.login_rate_limit_attempts:
        db.add(ActivityLog(admin_id=None, action="login_blocked", details=f"ip={ip};identifier={identifier}", ip_address=ip))
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, try again later",
        )
    LOGIN_ATTEMPTS[lock_key].append(now)
    admin = await db.scalar(
        select(AdminUser).where(
            or_(
                AdminUser.username == identifier,
                func.lower(AdminUser.email) == identifier.lower(),
            )
        )
    )
    if not admin or not verify_password(payload.password, admin.password_hash):
        db.add(ActivityLog(admin_id=None, action="login_failed", details=f"identifier={identifier}", ip_address=ip))
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    LOGIN_ATTEMPTS.pop(lock_key, None)
    expires_minutes = settings.jwt_remember_expires_minutes if payload.remember_me else settings.jwt_expires_minutes
    token = create_access_token(subject=admin.username, extra={"role": admin.role.value}, expires_minutes=expires_minutes)
    max_age = expires_minutes * 60
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.app_env.lower() == "prod",
        samesite="lax",
        path="/",
    )
    admin.last_login = now
    db.add(admin)
    db.add(ActivityLog(admin_id=admin.id, action="login", details="Admin login", ip_address=ip))
    await db.commit()
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=GenericMessage)
async def logout(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> GenericMessage:
    token = credentials.credentials if credentials else request.cookies.get("access_token")
    if token:
        revoke_token(token)
    response.delete_cookie("access_token", path="/")
    db.add(ActivityLog(admin_id=admin.id, action="logout", details="Admin logout"))
    await db.commit()
    return GenericMessage(message="logged_out")


@router.get("/me", response_model=GenericMessage)
async def me(admin: AdminUser = Depends(get_current_admin)) -> GenericMessage:
    return GenericMessage(message="ok", data={"username": admin.username, "role": admin.role.value})


@router.post("/request-reset", response_model=GenericMessage)
async def request_reset(payload: dict, db: AsyncSession = Depends(get_db)) -> GenericMessage:
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        raise HTTPException(status_code=422, detail="Identifier is required")
    admin = await db.scalar(
        select(AdminUser).where(
            or_(
                AdminUser.username == identifier,
                func.lower(AdminUser.email) == identifier.lower(),
            )
        )
    )
    # Always return success to avoid account enumeration.
    if not admin:
        return GenericMessage(message="reset_requested")
    token = secrets.token_urlsafe(24)
    PASSWORD_RESET_TOKENS[token] = (admin.username, datetime.utcnow() + timedelta(minutes=15))
    db.add(ActivityLog(admin_id=admin.id, action="password_reset_requested", details="via_auth_api"))
    await db.commit()
    return GenericMessage(message="reset_requested", data={"reset_token": token})


@router.post("/reset-password", response_model=GenericMessage)
async def reset_password(payload: dict, db: AsyncSession = Depends(get_db)) -> GenericMessage:
    token = str(payload.get("token", "")).strip()
    new_password = str(payload.get("new_password", "")).strip()
    if not token or len(new_password) < 8:
        raise HTTPException(status_code=422, detail="Token and strong password are required")
    token_data = PASSWORD_RESET_TOKENS.get(token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    username, expires_at = token_data
    if expires_at < datetime.utcnow():
        PASSWORD_RESET_TOKENS.pop(token, None)
        raise HTTPException(status_code=400, detail="Reset token expired")
    admin = await db.scalar(select(AdminUser).where(AdminUser.username == username))
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    admin.password_hash = hash_password(new_password)
    db.add(admin)
    db.add(ActivityLog(admin_id=admin.id, action="password_reset_completed", details="via_auth_api"))
    PASSWORD_RESET_TOKENS.pop(token, None)
    await db.commit()
    return GenericMessage(message="password_reset")
