from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import require_roles
from admin.api.schemas import GenericMessage
from admin.api.services import logs_csv
from database.models import ActivityLog, AdminUser
from database.session import get_db

router = APIRouter(prefix="/api/logs", tags=["logs"])


def _build_pdf(log_rows: list[dict]) -> bytes:
    lines = ["Activity logs report", "-------------------"]
    for row in log_rows:
        lines.append(f"{row['created_at']} | admin={row.get('admin_id')} | {row['action']} | {row.get('details') or ''}")
    body = "\n".join(lines).encode("latin-1", errors="replace")
    header = b"%PDF-1.1\n"
    stream = b"BT /F1 10 Tf 50 780 Td (" + body.replace(b"(", b"[").replace(b")", b"]").replace(b"\n", b") Tj T* (") + b") Tj ET"
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1>>endobj\n",
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n",
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode() + stream + b"\nendstream endobj\n",
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>endobj\n",
    ]
    offsets = [0]
    pdf = bytearray(header)
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode())
    return bytes(pdf)


async def _cleanup_old_logs(db: AsyncSession, retention_days: int = 90) -> None:
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    await db.execute(delete(ActivityLog).where(ActivityLog.created_at < cutoff))
    await db.commit()


@router.get("", response_model=GenericMessage)
async def logs(
    limit: int = Query(default=100, le=500),
    admin_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    _ = admin
    await _cleanup_old_logs(db)
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    if admin_id is not None:
        query = query.where(ActivityLog.admin_id == admin_id)
    if action:
        query = query.where(ActivityLog.action == action)
    if from_date:
        query = query.where(ActivityLog.created_at >= from_date)
    if to_date:
        query = query.where(ActivityLog.created_at <= to_date)
    rows = list((await db.scalars(query)).all())
    data = [
        {
            "id": row.id,
            "admin_id": row.admin_id,
            "action": row.action,
            "details": row.details,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
    return GenericMessage(message="ok", data={"items": data})


@router.get("/export")
async def export_logs(
    limit: int = Query(default=500, le=5000),
    format: str = Query(default="csv", pattern="^(csv|pdf)$"),
    admin_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> StreamingResponse:
    _ = admin
    await _cleanup_old_logs(db)
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(limit)
    if admin_id is not None:
        query = query.where(ActivityLog.admin_id == admin_id)
    if action:
        query = query.where(ActivityLog.action == action)
    if from_date:
        query = query.where(ActivityLog.created_at >= from_date)
    if to_date:
        query = query.where(ActivityLog.created_at <= to_date)
    rows = list((await db.scalars(query)).all())
    data = [
        {
            "id": row.id,
            "admin_id": row.admin_id,
            "action": row.action,
            "details": row.details,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
    if format == "pdf":
        return StreamingResponse(
            iter([_build_pdf(data)]),
            media_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="logs.pdf"'},
        )
    return StreamingResponse(
        iter([logs_csv(data)]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="logs.csv"'},
    )
