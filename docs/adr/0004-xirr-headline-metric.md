# XIRR is the headline performance metric

Performance is reported as money-weighted return (XIRR), matching what Indian AMC statements already show investors. XIRR accounts for the timing of every contribution and redemption, which matters for SIP-driven portfolios where a simple CAGR is misleading.

## Considered Options

- **Time-weighted return (TWR)**: better for judging a manager's skill, but it answers "is this fund good", not "did my money do well" — the question a wealth tracker is actually asked.
- **Absolute or percentage gain**: ignores timing entirely.

## Consequences

- XIRR requires a complete, correctly-classified Cash Flow series; a gap in the ledger produces a wrong number rather than an obviously broken one.
- Per-lot P&L is the companion view that exposes individual entry timing, which XIRR deliberately blends away.
