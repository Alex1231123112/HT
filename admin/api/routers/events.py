from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, require_roles, verify_csrf
from admin.api.schemas import (
    EventCreate,
    EventOut,
    EventRegistrationOut,
    EventUpdate,
    GenericMessage,
)
from database.models import ActivityLog, AdminUser, Event, EventRegistration, User, UserType
from database.session import get_db

router = APIRouter(prefix="/api/events", tags=["events"])


async def _event_to_out(db: AsyncSession, event: Event) -> EventOut:
    cnt = await db.scalar(
        select(func.count()).select_from(EventRegistration).where(EventRegistration.event_id == event.id)
    )
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description or "",
        image_url=event.image_url,
        user_type=event.user_type,
        event_date=event.event_date,
        location=event.location or "",
        is_active=event.is_active,
        max_places=event.max_places,
        created_at=event.created_at,
        registered_count=cnt or 0,
    )


@router.get("", response_model=list[EventOut])
async def list_events(
    user_type: UserType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[EventOut]:
    _ = admin
    query = select(Event).order_by(Event.event_date.asc())
    if user_type:
        query = query.where(or_(Event.user_type == user_type, Event.user_type == UserType.ALL))
    events = list((await db.scalars(query)).all())
    return [await _event_to_out(db, e) for e in events]


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> EventOut:
    _ = admin
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await _event_to_out(db, event)


@router.get("/{event_id}/registrations", response_model=list[EventRegistrationOut])
async def list_event_registrations(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[EventRegistrationOut]:
    _ = admin
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    result = await db.execute(
        select(EventRegistration, User)
        .join(User, User.id == EventRegistration.user_id)
        .where(EventRegistration.event_id == event_id)
        .order_by(EventRegistration.registered_at.asc())
    )
    rows = result.all()
    return [
        EventRegistrationOut(
            id=reg.id,
            event_id=reg.event_id,
            user_id=reg.user_id,
            registered_at=reg.registered_at,
            user_username=user.username,
            user_full_name=user.full_name,
            user_phone=user.phone_number,
            user_establishment=user.establishment,
        )
        for reg, user in rows
    ]


@router.post("", response_model=EventOut, dependencies=[Depends(verify_csrf)])
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin", "manager")),
) -> EventOut:
    event = Event(**payload.model_dump())
    db.add(event)
    db.add(ActivityLog(admin_id=admin.id, action="create_event", details=f"event={event.title}"))
    await db.commit()
    await db.refresh(event)
    return await _event_to_out(db, event)


@router.put("/{event_id}", response_model=EventOut, dependencies=[Depends(verify_csrf)])
async def update_event(
    event_id: int,
    payload: EventUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> EventOut:
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(event, key, value)
    db.add(event)
    db.add(ActivityLog(admin_id=admin.id, action="update_event", details=f"event_id={event_id}"))
    await db.commit()
    await db.refresh(event)
    return await _event_to_out(db, event)


@router.delete("/{event_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_roles("superadmin", "admin")),
) -> GenericMessage:
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    db.add(ActivityLog(admin_id=admin.id, action="delete_event", details=f"event_id={event_id}"))
    await db.commit()
    return GenericMessage(message="deleted")
