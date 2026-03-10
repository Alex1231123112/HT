from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.security import hash_password
from config.settings import get_settings
from database.models import AdminRole, AdminUser, SystemSetting

DEFAULT_SYSTEM_SETTINGS = {
    "backup_schedule": "0 2 * * *",
    "backup_retention_days": "30",
    "timezone": "Europe/Moscow",
}


async def ensure_default_system_settings(session: AsyncSession) -> None:
    """Создаёт дефолтные настройки при первом запуске, если их ещё нет."""
    for key, value in DEFAULT_SYSTEM_SETTINGS.items():
        if await session.get(SystemSetting, key) is None:
            session.add(SystemSetting(key=key, value=value))
    await session.commit()


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
