import time

import httpx
import pytest

pytestmark = pytest.mark.integration

BASE_URL = "http://localhost:8000/api"


def _login(client: httpx.Client, username: str, password: str) -> str:
    response = client.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_manager_cannot_update_settings():
    client = httpx.Client(timeout=10.0)
    super_token = _login(client, "admin", "change-me")
    username = f"rbac_manager_{int(time.time())}"
    create_resp = client.post(
        f"{BASE_URL}/admins",
        headers={"Authorization": f"Bearer {super_token}", "X-CSRF-Token": "dev-csrf"},
        json={"username": username, "password": "manager-pass-123", "role": "manager"},
    )
    assert create_resp.status_code == 200, create_resp.text

    manager_token = _login(client, username, "manager-pass-123")
    forbidden = client.put(
        f"{BASE_URL}/settings",
        headers={"Authorization": f"Bearer {manager_token}", "X-CSRF-Token": "dev-csrf"},
        json={"items": [{"key": "test_key", "value": "value"}]},
    )
    assert forbidden.status_code == 403
