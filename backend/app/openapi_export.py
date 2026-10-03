import json
import sys
from pathlib import Path

from app.main import app


def main() -> None:
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()  # type: ignore[misc]  # the OpenAPI document is an untyped dict
    out.write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")  # type: ignore[misc]


if __name__ == "__main__":
    main()
