# Ledger-first Positions, with snapshots as reconciliation

Each Position is reconstructed from an immutable ledger of Transactions; the holdings stated in an imported statement are a *reconciliation checkpoint*, not the source of truth. Because a CAMS statement only covers its own period, a first import seeds an **opening balance** Transaction so that derived positions match the stated holdings. This gives accurate per-lot P&L and XIRR without pretending we hold history the statement does not contain.

## Considered Options

- **Snapshot-only**: store dated holdings and diff them. Robust to missing history, but cannot compute per-lot P&L, cost basis, or money-weighted returns.
- **Ledger-only, history required**: correct but unusable, since statements do not reliably carry history from inception.

## Consequences

- Derived positions must be checked against every imported statement, and mismatches surfaced to the user rather than silently accepted.
- Opening balances are a first-class concept and must be distinguishable from real Transactions in reporting.
