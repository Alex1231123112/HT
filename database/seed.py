from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.security import hash_password
from config.settings import get_settings
from database.models import AdminRole, AdminUser


async def ensure_default_admin(session: AsyncSession) -> None:
    settings = get_settings()
    existing = await session.scalar(select(AdminUser).where(AdminUser.username == settings.admin_default_username))
    if existing:
        return
    admin = AdminUser(
        username=settings.admin_default_username,
        password_hash=hash_password(settings.admin_default_password),
        role=AdminRole.SUPERADMIN,
    )
    session.add(admin)
    await session.commit()
