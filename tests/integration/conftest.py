"""
Общий conftest для интеграционных тестов.
Даёт клиент через FastAPI TestClient — тесты работают в контейнере без поднятого API на порту.
"""
import pytest
from fastapi.testclient import TestClient

from admin.api.main import app


@pytest.fixture
def api_client():
    """Клиент для вызова API (in-process, без реального HTTP). Работает при запуске из контейнера."""
    with TestClient(app) as client:
        yield client
