import time

import httpx

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
    client = httpx.Client(timeout=10.0)
    headers = _auth_headers(client)
    user_id = int(time.time())
    user_response = client.post(
        f"{BASE_URL}/users",
        headers=headers,
        json={
            "id": user_id,
            "username": f"user_{user_id}",
            "first_name": "Test",
            "last_name": "User",
            "user_type": "horeca",
            "establishment": "Test Establishment",
            "is_active": True,
        },
    )
    assert user_response.status_code == 200, user_response.text

    create_response = client.post(
        f"{BASE_URL}/mailings",
        headers=headers,
        json={
            "text": "Test mailing",
            "target_type": "custom",
            "media_type": "none",
            "custom_targets": [user_id],
        },
    )
    assert create_response.status_code == 200, create_response.text
    mailing_id = create_response.json()["id"]

    preview_response = client.post(f"{BASE_URL}/mailings/{mailing_id}/preview", headers={"Authorization": headers["Authorization"]})
    assert preview_response.status_code == 200

    send_response = client.post(f"{BASE_URL}/mailings/{mailing_id}/send", headers=headers)
    assert send_response.status_code == 200

    stats_response = client.get(f"{BASE_URL}/mailings/{mailing_id}/stats", headers={"Authorization": headers["Authorization"]})
    assert stats_response.status_code == 200
    assert "sent" in stats_response.json()["data"]
