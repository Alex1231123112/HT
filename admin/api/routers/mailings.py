from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import GenericMessage, MailingCreate, MailingOut, MailingUpdate
from admin.api.services import dispatch_mailing
from database.models import ActivityLog, AdminUser, Mailing, MailingStat, MailingStatus
from database.session import get_db

router = APIRouter(prefix="/api/mailings", tags=["mailings"])


@router.get("", response_model=list[MailingOut])
async def list_mailings(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[MailingOut]:
    _ = admin
    return list((await db.scalars(select(Mailing).order_by(Mailing.created_at.desc()))).all())


@router.get("/{mailing_id}", response_model=MailingOut)
async def get_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> MailingOut:
    _ = admin
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    return mailing


@router.post("", response_model=MailingOut, dependencies=[Depends(verify_csrf)])
async def create_mailing(
    payload: MailingCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> MailingOut:
    status_value = MailingStatus.SCHEDULED if payload.scheduled_at else MailingStatus.DRAFT
    raw_payload = payload.model_dump()
    raw_payload.pop("speed", None)
    mailing = Mailing(**raw_payload, status=status_value)
    db.add(mailing)
    await db.flush()
    db.add(ActivityLog(admin_id=admin.id, action="create_mailing", details=f"mailing={mailing.id}"))
    await db.commit()
    await db.refresh(mailing)
    return mailing


@router.put("/{mailing_id}", response_model=MailingOut, dependencies=[Depends(verify_csrf)])
async def update_mailing(
    mailing_id: int,
    payload: MailingUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> MailingOut:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(mailing, key, value)
    db.add(mailing)
    db.add(ActivityLog(admin_id=admin.id, action="update_mailing", details=f"mailing={mailing_id}"))
    await db.commit()
    await db.refresh(mailing)
    return mailing


@router.delete("/{mailing_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    await db.delete(mailing)
    db.add(ActivityLog(admin_id=admin.id, action="delete_mailing", details=f"mailing={mailing_id}"))
    await db.commit()
    return GenericMessage(message="deleted")


@router.post("/{mailing_id}/preview", response_model=GenericMessage)
async def preview_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    return GenericMessage(message="preview", data={"text": mailing.text, "media": mailing.media_url})


@router.post("/{mailing_id}/send", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def send_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    if mailing.status == MailingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cancelled mailing cannot be sent")
    recipients = await dispatch_mailing(db, mailing)
    db.add(ActivityLog(admin_id=admin.id, action="send_mailing", details=f"mailing={mailing_id}, count={recipients}"))
    await db.commit()
    return GenericMessage(message="sent", data={"recipients": recipients})


@router.post("/{mailing_id}/cancel", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def cancel_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    mailing.status = MailingStatus.CANCELLED
    mailing.cancelled_at = datetime.utcnow()
    db.add(mailing)
    db.add(ActivityLog(admin_id=admin.id, action="cancel_mailing", details=f"mailing={mailing_id}"))
    await db.commit()
    return GenericMessage(message="cancelled")


@router.post("/{mailing_id}/retry", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def retry_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    if mailing.status == MailingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cancelled mailing cannot be retried")
    recipients = await dispatch_mailing(db, mailing)
    db.add(ActivityLog(admin_id=admin.id, action="retry_mailing", details=f"mailing={mailing_id}, count={recipients}"))
    await db.commit()
    return GenericMessage(message="retried", data={"recipients": recipients})


@router.post("/{mailing_id}/test-send", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def test_send_mailing(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    mailing = await db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    db.add(ActivityLog(admin_id=admin.id, action="test_send_mailing", details=f"mailing={mailing_id}"))
    await db.commit()
    return GenericMessage(message="test_sent", data={"mailing_id": mailing_id})


@router.get("/{mailing_id}/stats", response_model=GenericMessage)
async def mailing_stats(
    mailing_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    sent = await db.scalar(select(func.count(MailingStat.id)).where(MailingStat.mailing_id == mailing_id)) or 0
    opened = await db.scalar(
        select(func.count(MailingStat.id)).where(MailingStat.mailing_id == mailing_id, MailingStat.opened_at.is_not(None))
    ) or 0
    clicked = await db.scalar(
        select(func.count(MailingStat.id)).where(
            MailingStat.mailing_id == mailing_id, MailingStat.clicked_at.is_not(None)
        )
    ) or 0
    ctr = round((clicked / sent) * 100, 2) if sent else 0
    open_rate = round((opened / sent) * 100, 2) if sent else 0
    return GenericMessage(
        message="ok",
        data={"sent": sent, "opened": opened, "clicked": clicked, "open_rate": open_rate, "ctr": ctr},
    )


async def process_due_mailings(db: AsyncSession) -> int:
    due = list(
        (
            await db.scalars(
                select(Mailing).where(
                    Mailing.status == MailingStatus.SCHEDULED,
                    Mailing.scheduled_at.is_not(None),
                    Mailing.scheduled_at <= datetime.utcnow(),
                )
            )
        ).all()
    )
    processed = 0
    for mailing in due:
        if mailing.status == MailingStatus.CANCELLED:
            continue
        try:
            await dispatch_mailing(db, mailing)
        except Exception:
            # Next worker cycle may retry this mailing manually or by scheduled policy.
            pass
        processed += 1
    return processed
