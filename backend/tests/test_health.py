"""Tests for GET /health."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body_keys() -> None:
    response = client.get("/health")
    body = response.json()
    assert set(body.keys()) == {"status", "version", "schema_revision"}


def test_health_status_is_ok() -> None:
    response = client.get("/health")
    assert response.json()["status"] == "ok"


def test_health_version_is_semver_string() -> None:
    response = client.get("/health")
    version = response.json()["version"]
    assert isinstance(version, str)
    assert "." in version


def test_health_schema_revision_is_null() -> None:
    response = client.get("/health")
    assert response.json()["schema_revision"] is None
