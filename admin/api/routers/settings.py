import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import GenericMessage, SettingBatch
from database.models import ActivityLog, AdminUser, SystemSetting
from database.session import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])
BACKUP_DIR = Path("e:/HT/backups")


@router.get("", response_model=GenericMessage)
async def get_settings_api(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    items = list((await db.scalars(select(SystemSetting))).all())
    return GenericMessage(message="ok", data={item.key: item.value for item in items})


@router.put("", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def put_settings(
    payload: SettingBatch,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    for item in payload.items:
        existing = await db.get(SystemSetting, item.key)
        if existing:
            existing.value = item.value
            db.add(existing)
        else:
            db.add(SystemSetting(key=item.key, value=item.value))
    db.add(ActivityLog(admin_id=admin.id, action="update_settings", details=f"count={len(payload.items)}"))
    await db.commit()
    return GenericMessage(message="saved")


@router.post("/backup", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def create_backup(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    items = list((await db.scalars(select(SystemSetting))).all())
    data = {item.key: item.value for item in items}
    filename = f"settings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    target = BACKUP_DIR / filename
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    db.add(ActivityLog(admin_id=admin.id, action="settings_backup", details=filename))
    await db.commit()
    return GenericMessage(message="backup_created", data={"filename": filename})


@router.get("/backups", response_model=GenericMessage)
async def list_backups(admin: AdminUser = Depends(require_roles("superadmin", "admin"))) -> GenericMessage:
    _ = admin
    if not BACKUP_DIR.exists():
        return GenericMessage(message="ok", data={"files": []})
    files = sorted([item.name for item in BACKUP_DIR.glob("settings_*.json")], reverse=True)
    return GenericMessage(message="ok", data={"files": files})
