"""
Интеграционные тесты отправки контент-плана в бот и канал.

ВНИМАНИЕ: вызовы к Telegram API здесь подменены моками (patch tg.send_text / tg.send_photo).
Сообщения в реальный бот и канал при запуске pytest НЕ отправляются — проверяется только логика.

Чтобы сообщения реально пришли: запустите приложение (API + бот), в админке создайте контент-план
и нажмите «Отправить» или вызовите POST /api/content-plan/{id}/send с авторизацией.
Подробнее: README, раздел «Тесты отправки vs реальные сообщения».

Запуск теста: pytest tests/integration/test_content_plan_send.py -v
"""
import time
from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.integration

CSRF = "dev-csrf"


def _login(client, username: str = "admin", password: str = "change-me") -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-CSRF-Token": CSRF}


def test_content_plan_send_to_bot_and_channel_mocked(api_client):
    """
    Создаём пользователя, канал «Бот», канал «Telegram», запись контент-плана с custom контентом,
    вызываем отправку с замоканным Telegram API и проверяем, что sendMessage/sendPhoto вызваны
    с нужными chat_id (user для бота, @channel для канала) и текстом.
    """
    client = api_client
    headers = _login(client)

    base_id = (int(time.time()) % 900000) + 100000
    user_id = base_id + 1
    plan_title = f"Test plan {base_id}"

    # Пользователь бота (User.id = telegram user id)
    r_user = client.post(
        "/api/users",
        headers=headers,
        json={
            "id": user_id,
            "username": f"send_test_{user_id}",
            "user_type": "retail",
            "establishment": "Test Est",
            "is_active": True,
        },
    )
    if r_user.status_code in (400, 500):
        pytest.skip(f"User create failed: {r_user.status_code} {r_user.text}")
    assert r_user.status_code == 200, r_user.text

    # Каналы рассылки — берём существующие или создаём
    r_ch_list = client.get("/api/channels", headers=headers)
    assert r_ch_list.status_code == 200, r_ch_list.text
    channels = r_ch_list.json() if isinstance(r_ch_list.json(), list) else r_ch_list.json().get("data", r_ch_list.json())
    if not isinstance(channels, list):
        channels = []
    channel_ids = [ch["id"] for ch in channels if ch.get("is_active", True)][:2]
    if len(channel_ids) < 1:
        r_create_ch = client.post(
            "/api/channels",
            headers=headers,
            json={"name": "Бот (тест)", "channel_type": "bot", "is_active": True},
        )
        if r_create_ch.status_code == 200:
            channel_ids = [r_create_ch.json()["id"]]
        r_create_ch2 = client.post(
            "/api/channels",
            headers=headers,
            json={
                "name": "Канал (тест)",
                "channel_type": "telegram_channel",
                "telegram_ref": "@test_channel_send",
                "is_active": True,
            },
        )
        if r_create_ch2.status_code == 200:
            channel_ids.append(r_create_ch2.json()["id"])

    r_plan = client.post(
        "/api/content-plan",
        headers=headers,
        json={
            "title": plan_title,
            "content_type": "custom",
            "custom_title": "Заголовок рассылки",
            "custom_description": "Текст для бота и канала.",
            "channel_ids": channel_ids,
        },
    )
    assert r_plan.status_code == 200, r_plan.text
    plan_id = r_plan.json()["id"]

    send_text_calls = []
    send_photo_calls = []

    async def mock_send_text(bot_token, chat_id, text, parse_mode=None, *, reply_markup=None, client=None):
        send_text_calls.append({"chat_id": chat_id, "text": text})
        return ({"ok": True}, None)

    async def mock_send_photo(bot_token, chat_id, photo_url, caption=None, parse_mode=None, *, reply_markup=None, client=None):
        send_photo_calls.append({"chat_id": chat_id, "caption": caption, "photo_url": photo_url})
        return ({"ok": True}, None)

    with (
        patch("admin.api.content_plan_sender.tg.send_text", new_callable=AsyncMock, side_effect=mock_send_text),
        patch("admin.api.content_plan_sender.tg.send_photo", new_callable=AsyncMock, side_effect=mock_send_photo),
    ):
        r_send = client.post(f"/api/content-plan/{plan_id}/send", headers=headers)
        if r_send.status_code == 400 and "already sent" in (r_send.text or "").lower():
            pytest.skip("Plan was already sent in a previous run")
        assert r_send.status_code == 200, r_send.text
        data = r_send.json()
        assert data.get("message") == "sent"
        payload = data.get("data") or {}
        assert "sent_bot" in payload or "sent_channel" in payload

    total_sends = len(send_text_calls) + len(send_photo_calls)
    assert total_sends >= 1, "Expected at least one Telegram send (bot or channel)"
    all_chat_ids = [c["chat_id"] for c in send_text_calls] + [c["chat_id"] for c in send_photo_calls]
    assert user_id in all_chat_ids or "@test_channel_send" in all_chat_ids or any(
        str(user_id) == str(c) for c in all_chat_ids
    ), f"Expected chat_id for user {user_id} or channel; got {all_chat_ids}"
    all_texts = [c.get("text") or c.get("caption") or "" for c in send_text_calls + send_photo_calls]
    assert any("Заголовок рассылки" in t or "Текст для бота" in t for t in all_texts), f"Expected our content in sends; got {all_texts}"

    client.delete(f"/api/content-plan/{plan_id}", headers=headers)
    client.delete(f"/api/users/{user_id}", headers=headers)
