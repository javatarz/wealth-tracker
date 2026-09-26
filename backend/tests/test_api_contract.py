"""API contract tests against the committed OpenAPI spec."""

from __future__ import annotations

import json
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parent.parent.parent / "shared" / "openapi.json"


def _load_spec() -> dict[str, object]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def test_openapi_spec_is_valid_json() -> None:
    """The committed spec must be valid JSON with required OpenAPI keys."""
    spec = _load_spec()
    assert "openapi" in spec
    assert "paths" in spec


def test_health_response_conforms_to_spec() -> None:
    """A real /health response must validate against the committed spec."""
    from dataclasses import dataclass

    from fastapi.testclient import TestClient
    from openapi_core import OpenAPI
    from openapi_core.datatypes import RequestParameters

    from app.main import app

    spec_dict = _load_spec()
    openapi = OpenAPI.from_dict(spec_dict)  # type: ignore[arg-type]

    client = TestClient(app)
    response = client.get("/health")
    httpx_req = response.request
    httpx_resp = response

    # Thin wrappers satisfying openapi_core.protocols.Request / Response.
    @dataclass
    class OAPIRequest:
        host_url: str
        path: str
        method: str
        parameters: RequestParameters
        content_type: str
        body: bytes | None

    @dataclass
    class OAPIResponse:
        status_code: int
        headers: dict[str, str]  # type: ignore[assignment]
        content_type: str
        data: bytes | None

    wrapped_req = OAPIRequest(
        host_url=str(httpx_req.url),
        path=httpx_req.url.path,
        method=httpx_req.method.lower(),
        parameters=RequestParameters(
            query=dict(httpx_req.url.params),  # type: ignore[call-arg]
            header=dict(httpx_req.headers),  # type: ignore[call-arg]
            cookie={},
        ),
        content_type=httpx_req.headers.get("Content-Type", "application/octet-stream"),
        body=httpx_req.read() if httpx_req.content else None,
    )
    wrapped_resp = OAPIResponse(
        status_code=httpx_resp.status_code,
        headers=dict(httpx_resp.headers),
        content_type=httpx_resp.headers.get("Content-Type", ""),
        data=httpx_resp.content,
    )

    # validate_response raises on validation errors.
    openapi.validate_response(request=wrapped_req, response=wrapped_resp)  # type: ignore[arg-type]
