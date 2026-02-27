import httpx

BASE_URL = "http://localhost:8000/api"


def _auth_headers(client: httpx.Client) -> dict[str, str]:
    response = client.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "change-me"})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-CSRF-Token": "dev-csrf"}


def test_backup_creation_and_download():
    client = httpx.Client(timeout=10.0)
    headers = _auth_headers(client)
    create_response = client.post(f"{BASE_URL}/settings/backup", headers=headers)
    assert create_response.status_code == 200
    filename = create_response.json()["data"]["filename"]

    list_response = client.get(f"{BASE_URL}/settings/backups", headers={"Authorization": headers["Authorization"]})
    assert list_response.status_code == 200
    assert filename in list_response.json()["data"]["files"]

    download_response = client.get(f"{BASE_URL}/settings/backups/{filename}", headers={"Authorization": headers["Authorization"]})
    assert download_response.status_code == 200
