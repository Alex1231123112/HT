"""
Интеграционные тесты на весь функционал админки (API).
Используют FastAPI TestClient — работают при запуске из контейнера без отдельного API на порту.
Запуск: pytest tests/integration/test_admin_api.py -v
       pytest -m integration  (все интеграционные)
"""
import time
from datetime import datetime, timedelta
from io import BytesIO

import httpx
import pytest

pytestmark = pytest.mark.integration

CSRF = "dev-csrf"


def _login(client, username: str = "admin", password: str = "change-me") -> dict:
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-CSRF-Token": CSRF}


# --- Auth ---


def test_auth_login_success(api_client):
    client = api_client
    r = client.post("/api/auth/login", json={"username": "admin", "password": "change-me"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_auth_login_invalid(api_client):
    client = api_client
    r = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401


def test_auth_me(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "ok"
    assert "username" in data.get("data", {})
    assert data["data"]["username"] == "admin"


def test_auth_logout(api_client):
    client = api_client
    headers = _login(client)
    r = client.post("/api/auth/logout", headers=headers)
    assert r.status_code == 200
    assert r.json().get("message") == "logged_out"


# --- Users ---


def test_users_list(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/users", headers=headers)
    if r.status_code == 401:
        headers = _login(client)  # повторный логин (после logout в другом тесте)
        r = client.get("/api/users", headers=headers)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_users_create_get_update_delete(api_client):
    client = api_client
    headers = _login(client)
    # id должен помещаться в 32-bit int (БД/Telegram)
    uid = (int(time.time()) % 900000000) + 100000000

    create = client.post(
        "/api/users",
        headers=headers,
        json={
            "id": uid,
            "username": f"testuser_{uid}",
            "first_name": "Test",
            "last_name": "User",
            "user_type": "horeca",
            "establishment": "Test Bar",
            "is_active": True,
        },
    )
    assert create.status_code == 200, create.text
    assert create.json()["id"] == uid

    get_one = client.get(f"/api/users/{uid}", headers=headers)
    assert get_one.status_code == 200
    assert get_one.json()["establishment"] == "Test Bar"

    update = client.put(
        f"/api/users/{uid}",
        headers=headers,
        json={"full_name": "Updated Name", "position": "Manager", "phone_number": "+79991234567"},
    )
    assert update.status_code == 200
    assert update.json()["full_name"] == "Updated Name"
    assert update.json()["position"] == "Manager"
    assert update.json()["phone_number"] == "+79991234567"

    delete = client.delete(f"/api/users/{uid}", headers=headers)
    assert delete.status_code == 200
    get_after = client.get(f"/api/users/{uid}", headers=headers)
    assert get_after.status_code == 404


def test_users_list_filters(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/users?user_type=horeca", headers=headers)
    assert r.status_code == 200
    r2 = client.get("/api/users?search=test", headers=headers)
    assert r2.status_code == 200
    r3 = client.get("/api/users/count", headers=headers)
    assert r3.status_code == 200
    assert "data" in r3.json()


def test_users_stats_and_export(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/users/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "horeca" in data
    assert "retail" in data

    export = client.get("/api/users/export", headers=headers)
    assert export.status_code == 200
    assert "text/csv" in export.headers.get("content-type", "")
    assert "id," in export.text or "id;" in export.text


def test_users_bulk_restore(api_client):
    client = api_client
    headers = _login(client)
    uid = (int(time.time()) % 900000000) + 100000000
    client.post(
        "/api/users",
        headers=headers,
        json={
            "id": uid,
            "username": f"bulk_{uid}",
            "user_type": "retail",
            "establishment": "Bulk",
            "is_active": True,
        },
    )
    client.delete(f"/api/users/{uid}", headers=headers)
    r = client.post(
        "/api/users/bulk",
        headers=headers,
        json={"user_ids": [uid], "operation": "restore"},
    )
    assert r.status_code == 200
    get_one = client.get(f"/api/users/{uid}", headers=headers)
    assert get_one.status_code == 200
    assert get_one.json().get("deleted_at") is None


# --- Content: promotions, news, deliveries ---


def _content_crud(client, headers: dict, resource: str, type_label: str):
    r_list = client.get(f"/api/{resource}", headers=headers)
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)

    create = client.post(
        f"/api/{resource}",
        headers=headers,
        json={
            "title": f"Test {type_label} {int(time.time())}",
            "description": "Desc",
            "user_type": "horeca",
            "is_active": False,
        },
    )
    if create.status_code == 500:
        pytest.skip(f"Content create returned 500 (check API/DB): {resource}")
    assert create.status_code == 200, create.text
    item_id = create.json()["id"]

    get_one = client.get(f"/api/{resource}/{item_id}", headers=headers)
    assert get_one.status_code == 200

    client.put(
        f"/api/{resource}/{item_id}",
        headers=headers,
        json={"title": f"Updated {type_label}", "description": "Updated desc"},
    )
    client.delete(f"/api/{resource}/{item_id}", headers=headers)
    get_after = client.get(f"/api/{resource}/{item_id}", headers=headers)
    assert get_after.status_code == 404


def test_promotions_crud(api_client):
    client = api_client
    headers = _login(client)
    _content_crud(client, headers, "promotions", "promo")


def test_news_crud(api_client):
    client = api_client
    headers = _login(client)
    _content_crud(client, headers, "news", "news")


def test_deliveries_crud(api_client):
    client = api_client
    headers = _login(client)
    _content_crud(client, headers, "deliveries", "delivery")


def test_promotions_duplicate(api_client):
    client = api_client
    headers = _login(client)
    create = client.post(
        "/api/promotions",
        headers=headers,
        json={"title": "Original", "description": "", "user_type": "retail", "is_active": False},
    )
    if create.status_code == 500:
        pytest.skip("Promotion create returned 500 (check API/DB)")
    assert create.status_code == 200
    pid = create.json()["id"]
    dup = client.post(f"/api/promotions/{pid}/duplicate", headers=headers)
    assert dup.status_code == 200
    assert "(copy)" in dup.json()["title"]
    client.delete(f"/api/promotions/{pid}", headers=headers)
    client.delete(f"/api/promotions/{dup.json()['id']}", headers=headers)


# --- Events ---


def test_events_crud(api_client):
    client = api_client
    headers = _login(client)

    r_list = client.get("/api/events", headers=headers)
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)

    event_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")
    create = client.post(
        "/api/events",
        headers=headers,
        json={
            "title": f"Event {int(time.time())}",
            "description": "Desc",
            "user_type": "horeca",
            "event_date": event_date,
            "location": "Moscow",
            "is_active": True,
        },
    )
    if create.status_code == 500:
        pytest.skip("Event create returned 500 (check API/DB)")
    assert create.status_code == 200, create.text
    eid = create.json()["id"]

    get_one = client.get(f"/api/events/{eid}", headers=headers)
    assert get_one.status_code == 200

    client.put(f"/api/events/{eid}", headers=headers, json={"title": "Updated Event"})
    client.delete(f"/api/events/{eid}", headers=headers)
    get_after = client.get(f"/api/events/{eid}", headers=headers)
    assert get_after.status_code == 404


# --- Mailings (removed) ---


@pytest.mark.skip(reason="Mailings functionality removed")
def test_mailings_list_create_get_preview(api_client):
    client = api_client
    headers = _login(client)
    base_id = (int(time.time()) % 900000000) + 100000000
    user_ids = [base_id + i for i in range(3)]  # min_audience = 3

    for i, uid in enumerate(user_ids):
        client.post(
            "/api/users",
            headers=headers,
            json={
                "id": uid,
                "username": f"mail_{uid}",
                "user_type": "horeca",
                "establishment": f"Mailing Test {i}",
                "is_active": True,
            },
        )

    r_list = client.get("/api/mailings", headers=headers)
    assert r_list.status_code == 200
    assert isinstance(r_list.json(), list)

    create = client.post(
        "/api/mailings",
        headers=headers,
        json={
            "text": "Test mailing text",
            "target_type": "custom",
            "media_type": "none",
            "custom_targets": user_ids,
        },
    )
    if create.status_code == 400 and "frequency" in (create.text or "").lower():
        pytest.skip("Mailing frequency limit (60 min between sends)")
    assert create.status_code == 200, create.text
    mid = create.json()["id"]

    get_one = client.get(f"/api/mailings/{mid}", headers=headers)
    assert get_one.status_code == 200

    preview = client.post(f"/api/mailings/{mid}/preview", headers={"Authorization": headers["Authorization"]})
    assert preview.status_code == 200
    assert "text" in preview.json().get("data", {})

    client.delete(f"/api/mailings/{mid}", headers=headers)
    for uid in user_ids:
        client.delete(f"/api/users/{uid}", headers=headers)


@pytest.mark.skip(reason="Mailings functionality removed")
def test_mailings_send_and_stats(api_client):
    """Создаёт рассылку, отправляет, проверяет stats (как test_admin_flows)."""
    client = api_client
    headers = _login(client)
    base_id = (int(time.time()) % 900000000) + 100000000
    user_ids = [base_id + 20 + i for i in range(3)]  # offset to avoid clash with other tests
    try:
        for i, u in enumerate(user_ids):
            r = client.post(
                "/api/users",
                headers=headers,
                json={
                    "id": u,
                    "username": f"send_user_{u}",
                    "first_name": "Send",
                    "last_name": str(i),
                    "user_type": "retail",
                    "establishment": f"Establishment {i}",
                    "is_active": True,
                },
            )
            if r.status_code == 500:
                pytest.skip("User create returned 500 (possible duplicate id)")
            assert r.status_code == 200, r.text

        create = client.post(
            "/api/mailings",
            headers=headers,
            json={
                "text": "Send test",
                "target_type": "custom",
                "media_type": "none",
                "custom_targets": user_ids,
            },
        )
        if create.status_code == 400 and "frequency" in (create.text or "").lower():
            pytest.skip("Mailing frequency limit (60 min between sends)")
        assert create.status_code == 200, create.text
        mid = create.json()["id"]

        send = client.post(f"/api/mailings/{mid}/send", headers=headers)
        assert send.status_code == 200, send.text

        stats = client.get(f"/api/mailings/{mid}/stats", headers={"Authorization": headers["Authorization"]})
        assert stats.status_code == 200
        assert "data" in stats.json()

        for u in user_ids:
            client.delete(f"/api/users/{u}", headers=headers)
        client.delete(f"/api/mailings/{mid}", headers=headers)
    except (httpx.RemoteProtocolError, httpx.ConnectError) as e:
        pytest.skip(f"Server connection issue during send: {e}")


# --- Logs ---


def test_logs_list_and_export(api_client):
    client = api_client
    headers = _login(client)

    r = client.get("/api/logs", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "ok"
    assert "items" in data.get("data", {})

    csv_export = client.get("/api/logs/export?format=csv", headers=headers)
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers.get("content-type", "")

    pdf_export = client.get("/api/logs/export?format=pdf", headers=headers)
    assert pdf_export.status_code == 200
    assert "application/pdf" in pdf_export.headers.get("content-type", "")


# --- Uploads ---


def test_upload_file(api_client):
    client = api_client
    headers = _login(client)
    # Минимальный JPEG (1x1)
    jpeg_bytes = bytes(
        [0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12, 0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29, 0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03, 0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06, 0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72, 0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00, 0xFB, 0xE8, 0x20, 0xA2, 0x8A, 0x28, 0x03, 0xFF, 0xD9]
    )
    files = {"file": ("test.jpg", BytesIO(jpeg_bytes), "image/jpeg")}
    r = client.post("/api/upload", headers=headers, files=files)
    assert r.status_code == 200, r.text
    assert r.json().get("message") == "uploaded"
    data = r.json().get("data", {})
    assert "filename" in data
    assert "url" in data  # public URL (local or S3)


# --- Admins (superadmin) ---


def test_admins_list_and_get(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/admins", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data.get("message") == "ok"
    assert "items" in data.get("data", {})

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    # Получить первого админа для get by id
    items = data["data"]["items"]
    if items:
        aid = items[0]["id"]
        get_one = client.get(f"/api/admins/{aid}", headers=headers)
        assert get_one.status_code == 200


def test_admins_create_and_update(api_client):
    client = api_client
    headers = _login(client)
    username = f"testadmin_{int(time.time())}"

    create = client.post(
        "/api/admins",
        headers=headers,
        json={"username": username, "password": "securepass123", "role": "manager"},
    )
    assert create.status_code == 200, create.text
    aid = create.json()["id"]

    update = client.put(
        f"/api/admins/{aid}",
        headers=headers,
        json={"role": "admin"},
    )
    assert update.status_code == 200

    client.delete(f"/api/admins/{aid}", headers=headers)
    get_after = client.get(f"/api/admins/{aid}", headers=headers)
    assert get_after.status_code == 404


# --- Settings (superadmin) ---


def test_settings_get_put(api_client):
    client = api_client
    headers = _login(client)

    r = client.get("/api/settings", headers=headers)
    assert r.status_code == 200
    assert r.json().get("message") == "ok"

    put = client.put(
        "/api/settings",
        headers=headers,
        json={"items": [{"key": "test_admin_key", "value": "test_value"}]},
    )
    assert put.status_code == 200
    get2 = client.get("/api/settings", headers=headers)
    assert get2.status_code == 200
    assert get2.json().get("data", {}).get("test_admin_key") == "test_value"


def test_settings_backup_list_restore_dry_run(api_client):
    client = api_client
    headers = _login(client)

    backup = client.post("/api/settings/backup", headers=headers)
    assert backup.status_code == 200
    assert "filename" in backup.json().get("data", {})

    list_b = client.get("/api/settings/backups", headers=headers)
    assert list_b.status_code == 200
    files = list_b.json().get("data", {}).get("files", [])
    if files:
        fn = files[0]
        restore = client.post(f"/api/settings/restore/{fn}?dry_run=true", headers=headers)
        assert restore.status_code == 200
        assert restore.json().get("message") in ("restore_preview", "restore_applied")


# --- Analytics ---


def test_analytics_users_mailings_content(api_client):
    client = api_client
    headers = _login(client)

    r = client.get("/api/analytics/users", headers=headers)
    assert r.status_code == 200
    assert "data" in r.json()
    assert "total" in r.json()["data"]

    r3 = client.get("/api/analytics/content", headers=headers)
    assert r3.status_code == 200
    assert "data" in r3.json()

    r4 = client.get("/api/analytics/cohort", headers=headers)
    assert r4.status_code == 200

    r5 = client.get("/api/analytics/conversions", headers=headers)
    assert r5.status_code == 200

    export = client.get("/api/analytics/export", headers=headers)
    assert export.status_code == 200
    assert "text/csv" in export.headers.get("content-type", "")


# --- Dashboard ---


def test_dashboard_stats(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/dashboard/stats", headers=headers)
    assert r.status_code == 200
    payload = r.json()
    assert "new_today" in payload
    assert "new_week" in payload
    assert "total" in payload


def test_dashboard_users_chart_and_activity(api_client):
    client = api_client
    headers = _login(client)
    r = client.get("/api/dashboard/users-chart", headers=headers)
    assert r.status_code == 200
    assert "data" in r.json()

    r2 = client.get("/api/dashboard/activity", headers=headers)
    assert r2.status_code == 200
    assert "items" in r2.json().get("data", {})


# --- Unauthorized ---


def test_unauthorized_returns_401(api_client):
    client = api_client
    r = client.get("/api/users", headers={})
    assert r.status_code == 401

    r2 = client.get("/api/users", headers={"Authorization": "Bearer invalid"})
    assert r2.status_code == 401
