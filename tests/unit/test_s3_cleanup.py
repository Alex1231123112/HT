"""Юнит-тесты модуля s3_cleanup."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from admin.api.s3_cleanup import _extract_s3_key_from_url, _get_used_s3_keys


def test_extract_s3_key_from_url_s3_public():
    """Извлечение key из полного S3 URL."""
    assert _extract_s3_key_from_url("https://s3.example.com/bucket/uploads/abc123.jpg") == "uploads/abc123.jpg"
    assert _extract_s3_key_from_url("https://bucket.s3.region.amazonaws.com/uploads/photo.png") == "uploads/photo.png"
    assert _extract_s3_key_from_url("http://minio:9000/uploads/xyz.mp4") == "uploads/xyz.mp4"


def test_extract_s3_key_from_url_local_path():
    """Извлечение key из локального пути."""
    assert _extract_s3_key_from_url("/uploads/abc123.jpg") == "uploads/abc123.jpg"
    assert _extract_s3_key_from_url("/uploads/file.bin") == "uploads/file.bin"


def test_extract_s3_key_from_url_with_query():
    """URL с query string — key без query."""
    assert _extract_s3_key_from_url("https://x.com/uploads/a.jpg?token=1") == "uploads/a.jpg"


def test_extract_s3_key_from_url_invalid():
    """Невалидные URL возвращают None."""
    assert _extract_s3_key_from_url(None) is None
    assert _extract_s3_key_from_url("") is None
    assert _extract_s3_key_from_url("https://example.com/other/path") is None
    assert _extract_s3_key_from_url("https://example.com/uploads/../etc/passwd") is None


def test_extract_s3_key_from_url_path_traversal():
    """Защита от path traversal."""
    assert _extract_s3_key_from_url("/uploads/../etc/passwd") is None


@pytest.mark.asyncio
async def test_get_used_s3_keys_returns_extracted_keys():
    """_get_used_s3_keys возвращает ключи только от is_active записей (мок БД)."""
    urls = [
        ("https://s3.example.com/bucket/uploads/used1.jpg",),
        ("/uploads/used2.png",),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = urls

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_result)

    used = await _get_used_s3_keys(db)
    assert "uploads/used1.jpg" in used
    assert "uploads/used2.png" in used
    assert len(used) == 2
