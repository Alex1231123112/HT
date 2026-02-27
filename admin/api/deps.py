import hmac

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.security import decode_access_token, is_token_revoked
from config.settings import get_settings
from database.models import ActivityLog, AdminUser
from database.session import get_db

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if is_token_revoked(credentials.credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    admin = await db.scalar(select(AdminUser).where(AdminUser.username == username, AdminUser.is_active.is_(True)))
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    return admin


def verify_csrf(x_csrf_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not x_csrf_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing CSRF header")
    if settings.app_env.lower() == "prod" and settings.csrf_secret == "dev-csrf":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="CSRF secret is not configured")
    if not hmac.compare_digest(x_csrf_token, settings.csrf_secret):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def require_roles(*roles: str):
    async def _checker(
        admin: AdminUser = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db),
    ) -> AdminUser:
        if admin.role.value not in roles:
            db.add(ActivityLog(admin_id=admin.id, action="rbac_denied", details=f"required={','.join(roles)}"))
            await db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return admin

    return _checker
