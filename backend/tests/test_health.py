import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.unit
def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.text == '{"status":"ok"}'
