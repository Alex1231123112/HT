"""
Production smoke tests.
Run: PROD_URL=http://147.45.96.211:8000 pytest tests/prod/ -v
"""
import os

import pytest

pytestmark = [
    pytest.mark.prod,
    pytest.mark.skipif(not os.environ.get("PROD_URL"), reason="PROD_URL not set"),
]


def test_health(prod_client):
    """Health endpoint returns 200."""
    r = prod_client.get("/health")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("message") == "ok"


def test_metrics(prod_client):
    """Metrics endpoint returns Prometheus format."""
    r = prod_client.get("/metrics")
    assert r.status_code == 200, r.text
    assert "api_requests" in r.text or "python_" in r.text or "process_" in r.text or "http_" in r.text


def test_auth_rejects_invalid(prod_client):
    """Login с неверными данными возвращает 401."""
    r = prod_client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401
