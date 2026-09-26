"""Test that Alembic can run migrations against a fresh database."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory

from alembic.config import Config

from alembic import command


def test_migration_upgrade_to_head() -> None:
    """Run `alembic upgrade head` against a temp SQLite file and verify
    the alembic_version table records the head revision."""
    with TemporaryDirectory() as td:
        data_dir = Path(td) / "data"
        data_dir.mkdir()
        # Use the project's alembic.ini, but override sqlalchemy.url.
        alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
        cfg = Config(str(alembic_ini))
        cfg.set_main_option("sqlalchemy.url", f"sqlite:///{data_dir}/wealth.db")
        cfg.set_main_option(
            "script_location", str(Path(__file__).resolve().parent.parent / "alembic")
        )

        # Ensure backend is importable.
        backend_root = str(Path(__file__).resolve().parent.parent)
        orig_path = os.environ.get("PYTHONPATH", "")
        os.environ["PYTHONPATH"] = backend_root
        try:
            command.upgrade(cfg, "head")
        finally:
            os.environ["PYTHONPATH"] = orig_path

        # Verify the version stamp.
        import sqlite3

        conn = sqlite3.connect(str(data_dir / "wealth.db"))
        rows = conn.execute("SELECT version_num FROM alembic_version").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "0001"
