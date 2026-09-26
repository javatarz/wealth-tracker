"""baseline

Revision ID: 0001
Revises:
Create Date: 2026-09-26
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the initial schema (no tables yet — this is the baseline)."""


def downgrade() -> None:
    """No downgrade per ADR 0025 (forward-only migrations)."""