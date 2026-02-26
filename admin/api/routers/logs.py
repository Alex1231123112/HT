from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles
from admin.api.schemas import GenericMessage
from admin.api.services import logs_csv
from database.models import ActivityLog, AdminUser
from database.session import get_db

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=GenericMessage)
async def logs(
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    rows = list((await db.scalars(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit))).all())
    data = [
        {"id": row.id, "action": row.action, "details": row.details, "created_at": row.created_at.isoformat()}
        for row in rows
    ]
    return GenericMessage(message="ok", data={"items": data})


@router.get("/export")
async def export_logs(
    limit: int = Query(default=500, le=5000),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> StreamingResponse:
    _ = admin
    rows = list((await db.scalars(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit))).all())
    data = [
        {"id": row.id, "action": row.action, "details": row.details, "created_at": row.created_at.isoformat()}
        for row in rows
    ]
    return StreamingResponse(iter([logs_csv(data)]), media_type="text/csv")
