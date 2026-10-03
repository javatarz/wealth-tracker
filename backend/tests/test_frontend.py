from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

INDEX_HTML = "<!doctype html><title>Wealth Tracker</title>"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    (tmp_path / "index.html").write_text(INDEX_HTML)
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('hi');")
    return TestClient(create_app(Settings(static_dir=tmp_path)))


def test_root_serves_index(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.text == INDEX_HTML


def test_serves_built_assets(client: TestClient) -> None:
    response = client.get("/assets/app.js")

    assert response.status_code == 200
    assert response.text == "console.log('hi');"


def test_client_side_route_falls_back_to_index(client: TestClient) -> None:
    response = client.get("/goals/retirement")

    assert response.status_code == 200
    assert response.text == INDEX_HTML


def test_missing_asset_is_404(client: TestClient) -> None:
    assert client.get("/assets/missing.js").status_code == 404


def test_unknown_api_path_is_404_not_index(client: TestClient) -> None:
    assert client.get("/api/does-not-exist").status_code == 404


def test_api_still_served_alongside_frontend(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_no_frontend_mounted_without_static_dir() -> None:
    client = TestClient(create_app(Settings(static_dir=None)))

    assert client.get("/").status_code == 404
