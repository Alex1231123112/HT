from fastapi.testclient import TestClient

from admin.api.main import app

HEALTH_SLA_MS = 2000


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["message"] == "ok"


def test_health_response_time_sla():
    """Health endpoint must respond within SLA (target p95 < 500ms under load; in-process check uses 2s)."""
    client = TestClient(app)
    import time
    start = time.perf_counter()
    response = client.get("/health")
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert response.status_code == 200
    assert elapsed_ms < HEALTH_SLA_MS, f"/health took {elapsed_ms:.0f}ms, expected < {HEALTH_SLA_MS}ms"
