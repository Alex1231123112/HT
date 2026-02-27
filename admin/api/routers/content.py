from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from admin.api.deps import get_current_admin, verify_csrf
from admin.api.schemas import ContentCreate, ContentOut, ContentUpdate, GenericMessage
from admin.api.services import create_content, delete_content, get_content_by_id, list_content, update_content
from database.models import AdminUser, Delivery, News, Promotion, UserType
from database.session import get_db

router = APIRouter(prefix="/api", tags=["content"])


def ensure_manager_draft_only(admin: AdminUser, payload: dict) -> None:
    if admin.role.value != "manager":
        return
    if payload.get("is_active") is True:
        raise HTTPException(status_code=403, detail="Managers can only save drafts")
    if payload.get("published_at") is not None:
        raise HTTPException(status_code=403, detail="Managers cannot set publish date")


@router.get("/promotions", response_model=list[ContentOut])
async def promotions(
    user_type: UserType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[ContentOut]:
    _ = admin
    return await list_content(Promotion, db, user_type)


@router.get("/promotions/{item_id}", response_model=ContentOut)
async def get_promotion(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    _ = admin
    return await get_content_by_id(Promotion, item_id, db)


@router.post("/promotions", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def create_promotion(
    payload: ContentCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump()
    ensure_manager_draft_only(admin, data)
    return await create_content(Promotion, data, db)


@router.post("/promotions/{item_id}/duplicate", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def duplicate_promotion(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    _ = admin
    item = await get_content_by_id(Promotion, item_id, db)
    payload = {
        "title": f"{item.title} (copy)",
        "description": item.description,
        "image_url": item.image_url,
        "user_type": item.user_type,
        "published_at": item.published_at,
        "is_active": False,
    }
    return await create_content(Promotion, payload, db)


@router.put("/promotions/{item_id}", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def update_promotion(
    item_id: int,
    payload: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump(exclude_unset=True)
    ensure_manager_draft_only(admin, data)
    return await update_content(Promotion, item_id, data, db)


@router.delete("/promotions/{item_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_promotion(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    if admin.role.value == "manager":
        raise HTTPException(status_code=403, detail="Managers cannot delete published content")
    await delete_content(Promotion, item_id, db)
    return GenericMessage(message="deleted")


@router.get("/news", response_model=list[ContentOut])
async def news(
    user_type: UserType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[ContentOut]:
    _ = admin
    return await list_content(News, db, user_type)


@router.get("/news/{item_id}", response_model=ContentOut)
async def get_news(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    _ = admin
    return await get_content_by_id(News, item_id, db)


@router.post("/news", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def create_news(
    payload: ContentCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump()
    ensure_manager_draft_only(admin, data)
    return await create_content(News, data, db)


@router.put("/news/{item_id}", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def update_news(
    item_id: int,
    payload: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump(exclude_unset=True)
    ensure_manager_draft_only(admin, data)
    return await update_content(News, item_id, data, db)


@router.delete("/news/{item_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_news(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    if admin.role.value == "manager":
        raise HTTPException(status_code=403, detail="Managers cannot delete published content")
    await delete_content(News, item_id, db)
    return GenericMessage(message="deleted")


@router.get("/deliveries", response_model=list[ContentOut])
async def deliveries(
    user_type: UserType | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> list[ContentOut]:
    _ = admin
    return await list_content(Delivery, db, user_type)


@router.get("/deliveries/{item_id}", response_model=ContentOut)
async def get_delivery(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    _ = admin
    return await get_content_by_id(Delivery, item_id, db)


@router.post("/deliveries", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def create_delivery(
    payload: ContentCreate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump()
    ensure_manager_draft_only(admin, data)
    return await create_content(Delivery, data, db)


@router.put("/deliveries/{item_id}", response_model=ContentOut, dependencies=[Depends(verify_csrf)])
async def update_delivery(
    item_id: int,
    payload: ContentUpdate,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> ContentOut:
    data = payload.model_dump(exclude_unset=True)
    ensure_manager_draft_only(admin, data)
    return await update_content(Delivery, item_id, data, db)


@router.delete("/deliveries/{item_id}", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def delete_delivery(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    if admin.role.value == "manager":
        raise HTTPException(status_code=403, detail="Managers cannot delete published content")
    await delete_content(Delivery, item_id, db)
    return GenericMessage(message="deleted")
