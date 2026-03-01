import asyncio
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


def _upload_to_s3_sync(bucket: str, key: str, body: bytes, content_type: str) -> None:
    import boto3
    from botocore.config import Config

    client_kw: dict = {
        "service_name": "s3",
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": settings.s3_secret_access_key,
        "config": Config(signature_version="s3v4"),
    }
    if settings.s3_region:
        client_kw["region_name"] = settings.s3_region
    if settings.s3_endpoint_url:
        client_kw["endpoint_url"] = settings.s3_endpoint_url
    client = boto3.client(**client_kw)
    client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)


def _safe_extension(filename: str | None) -> str:
    """Расширение из имени файла или .bin."""
    if filename and "." in filename:
        ext = filename[filename.rfind(".") :].lower()
        if len(ext) <= 10 and ext.replace(".", "").isalnum():
            return ext
    return ".bin"


@router.post("/upload", response_model=GenericMessage, dependencies=[Depends(verify_csrf)])
async def upload_file(
    file: UploadFile = File(...),
    admin: AdminUser = Depends(get_current_admin),
) -> GenericMessage:
    _ = admin
    raw = await file.read()
    if len(raw) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    ext = _safe_extension(file.filename)
    safe_name = f"{uuid4().hex}{ext}"

    if settings.use_s3:
        bucket = settings.s3_bucket or ""
        key = f"uploads/{safe_name}"
        content_type = file.content_type or "application/octet-stream"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: _upload_to_s3_sync(bucket, key, raw, content_type),
        )
        if settings.s3_public_base_url:
            base = settings.s3_public_base_url.rstrip("/")
        elif settings.s3_endpoint_url:
            base = f"{settings.s3_endpoint_url.rstrip('/')}/{bucket}"
        else:
            region = settings.s3_region or "us-east-1"
            base = f"https://{bucket}.s3.{region}.amazonaws.com"
        public_url = f"{base}/{key}"
        return GenericMessage(
            message="uploaded",
            data={"filename": safe_name, "size": len(raw), "url": public_url},
        )
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / safe_name
    target.write_bytes(raw)
    base_url = (settings.upload_base_url or "").rstrip("/")
    local_url = f"{base_url}/{safe_name}" if base_url else f"/uploads/{safe_name}"
    return GenericMessage(
        message="uploaded",
        data={"filename": safe_name, "size": len(raw), "url": local_url},
    )
