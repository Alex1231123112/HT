import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import require_roles, verify_csrf
from admin.api.schemas import GenericMessage, SettingBatch
from config.settings import get_settings
from database.models import ActivityLog, AdminUser, SystemSetting
from database.session import get_db

router = APIRouter(prefix="/api/settings", tags=["settings"])
settings = get_settings()
BACKUP_DIR = Path(settings.backup_dir)


@router.get("", response_model=GenericMessage)
async def get_settings_api(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> GenericMessage:
    _ = admin
    items = list((await db.scalars(select(SystemSetting))).all())
    return GenericMessage(message="ok", data={item.key: item.value for item in items})


@router.put("", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def put_settings(
    payload: SettingBatch,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
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
    admin: AdminUser = Depends(require_roles("superadmin")),
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
async def list_backups(admin: AdminUser = Depends(require_roles("superadmin"))) -> GenericMessage:
    _ = admin
    if not BACKUP_DIR.exists():
        return GenericMessage(message="ok", data={"files": []})
    files = sorted([item.name for item in BACKUP_DIR.glob("settings_*.json")], reverse=True)
    return GenericMessage(message="ok", data={"files": files})


@router.get("/backups/{filename}")
async def download_backup(
    filename: str,
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> FileResponse:
    _ = admin
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    target = BACKUP_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Backup not found")
    return FileResponse(path=target, filename=filename, media_type="application/json")


@router.put("/backup-policy", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def update_backup_policy(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> GenericMessage:
    schedule = str(payload.get("schedule", "0 2 * * *"))
    retention_days = str(payload.get("retention_days", 30))
    for key, value in {"backup_schedule": schedule, "backup_retention_days": retention_days}.items():
        existing = await db.get(SystemSetting, key)
        if existing:
            existing.value = value
            db.add(existing)
        else:
            db.add(SystemSetting(key=key, value=value))
    db.add(ActivityLog(admin_id=admin.id, action="update_backup_policy", details=f"schedule={schedule}, retention={retention_days}"))
    await db.commit()
    return GenericMessage(message="backup_policy_saved")


@router.post("/restore/{filename}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def restore_backup(
    filename: str,
    dry_run: bool = True,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin")),
) -> GenericMessage:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    target = BACKUP_DIR / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="Backup not found")
    content = json.loads(target.read_text(encoding="utf-8"))
    if not dry_run:
        for key, value in content.items():
            existing = await db.get(SystemSetting, key)
            if existing:
                existing.value = str(value)
                db.add(existing)
            else:
                db.add(SystemSetting(key=key, value=str(value)))
    db.add(ActivityLog(admin_id=admin.id, action="restore_backup", details=f"{filename}, dry_run={dry_run}"))
    await db.commit()
    return GenericMessage(message="restore_preview" if dry_run else "restore_applied", data={"keys": list(content.keys())})
