from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from admin.api.deps import get_current_admin, verify_csrf
from admin.api.schemas import GenericMessage
from config.settings import get_settings
from database.models import AdminUser

router = APIRouter(prefix="/api", tags=["uploads"])
settings = get_settings()


@router.post("/upload", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def upload_file(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    allowed = {"image/jpeg", "image/png", "image/webp", "video/mp4"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Invalid MIME type")
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".mp4"}
    if file.filename and "." in file.filename:
        extension = file.filename[file.filename.rfind(".") :].lower()
        if extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file extension")
    return GenericMessage(message="uploaded", data={"filename": file.filename, "size": len(raw)})
