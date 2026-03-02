import time

import pytest

pytestmark = pytest.mark.integration


def _login(client, username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_manager_cannot_update_settings(api_client):
    client = api_client
    super_token = _login(client, "admin", "change-me")
    username = f"rbac_manager_{int(time.time())}"
    create_resp = client.post(
        "/api/admins",
        headers={"Authorization": f"Bearer {super_token}", "X-CSRF-Token": "dev-csrf"},
        json={"username": username, "password": "manager-pass-123", "role": "manager"},
    )
    assert create_resp.status_code == 200, create_resp.text

    manager_token = _login(client, username, "manager-pass-123")
    forbidden = client.put(
        "/api/settings",
        headers={"Authorization": f"Bearer {manager_token}", "X-CSRF-Token": "dev-csrf"},
        json={"items": [{"key": "test_key", "value": "value"}]},
    )
    assert forbidden.status_code == 403
