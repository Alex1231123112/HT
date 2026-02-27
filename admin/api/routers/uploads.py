from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from admin.api.deps import get_current_admin, verify_csrf
from admin.api.schemas import GenericMessage
from config.settings import get_settings
from database.models import AdminUser

router = APIRouter(prefix="/api", tags=["uploads"])
settings = get_settings()
UPLOAD_DIR = Path(settings.upload_dir)


def _detect_file_type(raw: bytes) -> str | None:
    if raw.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(raw) >= 12 and raw[0:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp"
    if b"ftyp" in raw[4:16]:
        return "video/mp4"
    return None


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
    detected = _detect_file_type(raw)
    if not detected:
        raise HTTPException(status_code=400, detail="Cannot detect file type")
    if file.content_type and file.content_type != detected:
        raise HTTPException(status_code=400, detail="MIME mismatch")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = extension if file.filename and "." in file.filename else {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "video/mp4": ".mp4",
    }[detected]
    safe_name = f"{uuid4().hex}{ext}"
    target = UPLOAD_DIR / safe_name
    target.write_bytes(raw)
    return GenericMessage(message="uploaded", data={"filename": safe_name, "size": len(raw)})
