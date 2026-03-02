"""Юнит-тесты отправки в Telegram (мок HTTP-клиента)."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from admin.api import telegram_sender as tg


@pytest.mark.asyncio
async def test_send_text_calls_telegram_api_with_mock_client():
    """send_text с подставным клиентом вызывает POST с нужным url и body."""
    calls = []

    async def mock_post(url, json=None, **kwargs):
        calls.append({"url": url, "json": json})
        res = MagicMock()
        res.is_success = True
        res.content = b'{"ok": true}'
        res.json.return_value = {"ok": True}
        return res

    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=mock_post)

    data, err = await tg.send_text(
        "fake-bot-token",
        12345,
        "<b>Test</b>",
        client=mock_client,
    )
    assert data == {"ok": True}
    assert err is None
    assert len(calls) == 1
    assert "api.telegram.org" in calls[0]["url"]
    assert "sendMessage" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == 12345
    assert "Test" in calls[0]["json"]["text"]


@pytest.mark.asyncio
async def test_send_photo_calls_telegram_api_with_mock_client():
    """send_photo с подставным клиентом вызывает POST с photo и caption."""
    calls = []

    async def mock_post(url, json=None, **kwargs):
        calls.append({"url": url, "json": json})
        res = MagicMock()
        res.is_success = True
        res.content = b'{"ok": true}'
        res.json.return_value = {"ok": True}
        return res

    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=mock_post)

    data, err = await tg.send_photo(
        "fake-bot-token",
        "@channel",
        "https://example.com/image.jpg",
        caption="<b>Caption</b>",
        client=mock_client,
    )
    assert data == {"ok": True}
    assert err is None
    assert len(calls) == 1
    assert "sendPhoto" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "@channel"
    assert calls[0]["json"]["photo"] == "https://example.com/image.jpg"
    assert "Caption" in calls[0]["json"]["caption"]
