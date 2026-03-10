"""Суточная очистка неиспользуемых файлов из S3."""

import asyncio
import logging
from urllib.parse import unquote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from database.models import Delivery, Event, News, Promotion

logger = logging.getLogger(__name__)

UPLOADS_PREFIX = "uploads/"


def _extract_s3_key_from_url(url: str | None) -> str | None:
    """
    Извлекает S3 key (uploads/xxx.ext) из URL.
    Для S3: https://.../bucket/uploads/abc.jpg -> uploads/abc.jpg.
    Для локального: /uploads/abc.jpg -> uploads/abc.jpg.
    Возвращает None если URL не наш или key невалиден.
    """
    if not url or not url.strip():
        return None
    url = url.strip()
    # Ищем uploads/ в пути
    if UPLOADS_PREFIX in url:
        idx = url.find(UPLOADS_PREFIX)
        rest = url[idx:]
        # Убираем query string
        if "?" in rest:
            rest = rest.split("?", 1)[0]
        key = unquote(rest)
        if not key.startswith(UPLOADS_PREFIX):
            return None
        if ".." in key:
            return None
        return key
    # Локальный путь /uploads/xxx
    if url.startswith("/uploads/"):
        key = url[1:]  # uploads/xxx
        if ".." in key:
            return None
        return key
    return None


async def _get_used_s3_keys(db: AsyncSession) -> set[str]:
    """
    Собирает все image_url из активного контента (Promotion, News, Delivery, Event)
    и извлекает S3 keys. Возвращает множество ключей.
    """
    used: set[str] = set()
    for model in (Promotion, News, Delivery, Event):
        rows = (
            await db.execute(
                select(model.image_url).where(model.is_active.is_(True), model.image_url.isnot(None))
            )
        ).scalars().all()
        for (url,) in rows:
            key = _extract_s3_key_from_url(url)
            if key:
                used.add(key)
    return used


def _create_s3_client():
    """Создаёт boto3 S3 client по настройкам (как в uploads.py)."""
    import boto3
    from botocore.config import Config

    st = get_settings()
    config = Config(signature_version="s3v4")
    if st.s3_endpoint_url:
        config = Config(signature_version="s3v4", s3={"addressing_style": "path"})
    client_kw: dict = {
        "service_name": "s3",
        "aws_access_key_id": st.s3_access_key_id,
        "aws_secret_access_key": st.s3_secret_access_key,
        "config": config,
    }
    if st.s3_region:
        client_kw["region_name"] = st.s3_region
    if st.s3_endpoint_url:
        client_kw["endpoint_url"] = st.s3_endpoint_url
    return boto3.client(**client_kw)


def _list_and_delete_unused_sync(bucket: str, used_keys: set[str]) -> int:
    """
    Синхронно: list_objects_v2 по префиксу uploads/, удаляет объекты не из used_keys.
    Возвращает количество удалённых.
    """
    client = _create_s3_client()
    deleted = 0
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=UPLOADS_PREFIX):
        for obj in page.get("Contents") or []:
            key = obj.get("Key")
            if not key or not key.startswith(UPLOADS_PREFIX) or ".." in key:
                continue
            if key in used_keys:
                continue
            try:
                client.delete_object(Bucket=bucket, Key=key)
                deleted += 1
                logger.info("S3 cleanup: deleted %s", key)
            except Exception as e:
                logger.warning("S3 cleanup: failed to delete %s: %s", key, e)
    return deleted


async def run_daily_s3_cleanup(db: AsyncSession) -> int:
    """
    Запуск суточной очистки S3.
    Собирает used keys из активного контента, перечисляет объекты в uploads/,
    удаляет неиспользуемые. Возвращает количество удалённых файлов.
    """
    st = get_settings()
    if not st.use_s3:
        return 0
    bucket = st.s3_bucket or ""
    if not bucket:
        return 0
    used_keys = await _get_used_s3_keys(db)
    loop = asyncio.get_running_loop()
    deleted = await loop.run_in_executor(None, _list_and_delete_unused_sync, bucket, used_keys)
    if deleted > 0:
        logger.info("S3 cleanup: removed %s unused file(s)", deleted)
    return deleted
