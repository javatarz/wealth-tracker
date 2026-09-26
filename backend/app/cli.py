"""CLI for development operations.

Usage::

    python -m app.cli export-openapi --output ../shared/openapi.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _export_openapi(output: Path) -> None:
    """Generate the OpenAPI spec and write it to *output*."""
    from app.main import app

    spec_dict: object = app.openapi()
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: str = json.dumps(spec_dict, indent=2, sort_keys=True) + "\n"
    output.write_text(payload, encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Wealth Tracker dev CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export-openapi", help="Write OpenAPI JSON to disk")
    export.add_argument(
        "--output",
        type=Path,
        default=Path("../shared/openapi.json"),
        help="Output path (default: ../shared/openapi.json)",
    )

    args = parser.parse_args(argv)
    command: str = args.command
    output: Path = args.output

    if command == "export-openapi":
        _export_openapi(output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
