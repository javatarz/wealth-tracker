"""Content fingerprints for statement-derived Transactions (ADR 0006).

The fingerprint is built from parsed output, so changing what goes into it changes
every fingerprint. Bump FINGERPRINT_VERSION when you do.
"""

import hashlib

from app.core.statement_preview import Transaction as StatementTransaction

FINGERPRINT_VERSION = "v1"


def transaction_fingerprint(ledger_key: str, row: StatementTransaction, occurrence: int) -> str:
    """`occurrence` tells apart identical rows in one statement (two same-day SIPs)."""
    parts = (
        FINGERPRINT_VERSION,
        ledger_key,
        row.date.isoformat(),
        row.type,
        row.units,
        row.amount,
        occurrence,
    )
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
