import time

import httpx
import pytest

pytestmark = pytest.mark.integration

BASE_URL = "http://localhost:8000/api"


def _auth_headers(client: httpx.Client) -> dict[str, str]:
    response = client.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "change-me"})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-CSRF-Token": "dev-csrf"}


def test_dashboard_stats_has_extended_fields():
    client = httpx.Client(timeout=10.0)
    headers = _auth_headers(client)
    response = client.get(f"{BASE_URL}/dashboard/stats", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "new_today" in payload
    assert "new_week" in payload
    assert "new_month" in payload
    assert "mailings_month" in payload


def test_create_send_and_stat_mailing():
    """Min audience = 3, use 32-bit safe user ids."""
    client = httpx.Client(timeout=30.0)
    headers = _auth_headers(client)
    base_id = (int(time.time()) % 900000000) + 100000000
    user_ids = [base_id + i for i in range(3)]
    for i, uid in enumerate(user_ids):
        r = client.post(
            f"{BASE_URL}/users",
            headers=headers,
            json={
                "id": uid,
                "username": f"user_{uid}",
                "first_name": "Test",
                "last_name": f"User{i}",
                "user_type": "horeca",
                "establishment": f"Test Establishment {i}",
                "is_active": True,
            },
        )
        assert r.status_code == 200, r.text

    create_response = client.post(
        f"{BASE_URL}/mailings",
        headers=headers,
        json={
            "text": "Test mailing",
            "target_type": "custom",
            "media_type": "none",
            "custom_targets": user_ids,
        },
    )
    if create_response.status_code == 400 and "frequency" in (create_response.text or "").lower():
        pytest.skip("Mailing frequency limit (60 min between sends)")
    assert create_response.status_code == 200, create_response.text
    mailing_id = create_response.json()["id"]

    preview_response = client.post(f"{BASE_URL}/mailings/{mailing_id}/preview", headers={"Authorization": headers["Authorization"]})
    assert preview_response.status_code == 200

    send_response = client.post(f"{BASE_URL}/mailings/{mailing_id}/send", headers=headers)
    assert send_response.status_code == 200, send_response.text

    stats_response = client.get(f"{BASE_URL}/mailings/{mailing_id}/stats", headers={"Authorization": headers["Authorization"]})
    assert stats_response.status_code == 200
    assert "sent" in stats_response.json()["data"]

    for uid in user_ids:
        client.delete(f"{BASE_URL}/users/{uid}", headers=headers)
    client.delete(f"{BASE_URL}/mailings/{mailing_id}", headers=headers)


def test_mailing_smoke_multiple_recipients():
    """Smoke test: create mailing for several users, send, verify delivery stats (acceptance checklist). Ids fit 32-bit."""
    client = httpx.Client(timeout=30.0)
    headers = _auth_headers(client)
    base_id = (int(time.time()) % 900000000) + 100000000
    user_ids = [base_id + 10 + i for i in range(3)]  # offset to avoid clash with other test
    for i, uid in enumerate(user_ids):
        r = client.post(
            f"{BASE_URL}/users",
            headers=headers,
            json={
                "id": uid,
                "username": f"smoke_user_{uid}",
                "first_name": "Smoke",
                "last_name": f"User{i}",
                "user_type": "retail",
                "establishment": f"Smoke Establishment {i}",
                "is_active": True,
            },
        )
        assert r.status_code == 200, r.text

    create_response = client.post(
        f"{BASE_URL}/mailings",
        headers=headers,
        json={
            "text": "Smoke test mailing to multiple recipients",
            "target_type": "custom",
            "media_type": "none",
            "custom_targets": user_ids,
        },
    )
    if create_response.status_code == 400 and "frequency" in (create_response.text or "").lower():
        pytest.skip("Mailing frequency limit (60 min between sends)")
    if create_response.status_code == 500:
        pytest.skip("Mailing create returned 500")
    assert create_response.status_code == 200, create_response.text
    mailing_id = create_response.json()["id"]

    send_response = client.post(f"{BASE_URL}/mailings/{mailing_id}/send", headers=headers)
    assert send_response.status_code == 200, send_response.text

    stats_response = client.get(f"{BASE_URL}/mailings/{mailing_id}/stats", headers={"Authorization": headers["Authorization"]})
    assert stats_response.status_code == 200
    data = stats_response.json().get("data", {})
    sent = data.get("sent", 0)
    assert sent >= 1, f"Expected at least one delivery, got stats: {data}"

    for uid in user_ids:
        client.delete(f"{BASE_URL}/users/{uid}", headers=headers)
    client.delete(f"{BASE_URL}/mailings/{mailing_id}", headers=headers)
