"""Verify the committed OpenAPI spec hasn't drifted from the running app."""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app

SPEC_PATH = Path(__file__).resolve().parent.parent.parent / "shared" / "openapi.json"


def test_openapi_spec_matches_app() -> None:
    """The committed shared/openapi.json must equal the live app.openapi()."""
    live = app.openapi()
    live_json = json.dumps(live, indent=2, sort_keys=True) + "\n"

    committed = SPEC_PATH.read_text(encoding="utf-8")
    assert live_json == committed, (
        "shared/openapi.json has drifted from app.openapi(). "
        "Run `mise run api:spec` and commit the result."
    )
