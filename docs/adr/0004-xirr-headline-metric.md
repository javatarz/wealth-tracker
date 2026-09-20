# XIRR is the headline performance metric

Performance is reported as money-weighted return (XIRR), matching what Indian AMC statements already show investors. XIRR accounts for the timing of every contribution and redemption, which matters for SIP-driven portfolios where a simple CAGR is misleading.

## Considered Options

- **Time-weighted return (TWR)**: better for judging a manager's skill, but it answers "is this fund good", not "did my money do well" — the question a wealth tracker is actually asked.
- **Absolute or percentage gain**: ignores timing entirely.

## Full metrics roster

The summary table (beside the growth graph) shows:

| Metric | Description | Scope |
|---|---|---|
| XIRR | Money-weighted return since inception | All cash-flow assets |
| Benchmark return | XIRR of the benchmark index over the same period | Where benchmark is set |
| P&L (₹) | Current value − total cost | All positions |
| P&L (%) | P&L ÷ total cost | All positions |
| Realized gain | P&L from closed lots | Equity, crypto, MF |
| Unrealized gain | P&L from open lots | Equity, crypto, MF |
| Sharpe ratio | (XIRR − Rf) ÷ σ of periodic returns | Cash-flow assets |

### Sharpe ratio

Formula: (Portfolio XIRR − Risk-free rate) ÷ Standard deviation of periodic
returns. Computed from the daily portfolio NAV series.

| Value | Meaning |
|---|---|
| < 0 | Worse than risk-free |
| 0–0.5 | Poor |
| 0.5–1 | Acceptable |
| 1–2 | Good |
| > 2 | Excellent |

The risk-free rate is the Indian 91-day Treasury Bill yield, sourced from the
market-data provider. If the provider does not carry T-bill history, fall back
to the 90-day FD rate of a major bank (e.g., SBI). Neither the NAV series nor
the Sharpe ratio is stored pre-computed — both are derived on-the-fly, so
changing the risk-free rate source requires no data migration.

### Return window

All metrics shown since inception only. No trailing-window columns.

### Portfolio-level aggregation

Portfolio XIRR is computed from the merged cash-flow series of all positions.
The headline tells the user "how is all my money doing together?" At asset
class or account level, show the weighted-average XIRR of child positions
(weighted by current market value). P&L (₹ and %) is always additive.

### Asset class relevance

| Metric | Equity/MF | Crypto | FD | PPF/EPF | Gold | RE (rented) | RE (owned) |
|---|---|---|---|---|---|---|---|
| XIRR | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |
| P&L | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Benchmark | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Yield / rate | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| CAGR | — | — | — | — | ✅ | — | ✅ |
| Sharpe | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

For accrual assets (FD, PPF, EPF), return is shown as the stated interest rate
rather than XIRR. For gold and owned real estate, return is price CAGR since
inception (based on appraisal history). Rented RE has a cash-flow stream
(purchase + rent income + current value) and qualifies for XIRR.

Benchmark defaults are configurable per asset class (see below).

### RE rental transitions

A single RE Instrument tracks both owned and rented periods. Rental income
enters the ledger as Income events (ADR 0003). The return engine reads all
cash flows on the Instrument:
- Never rented → CAGR + P&L
- Has rental income in ledger → XIRR + P&L + benchmark

The UI shows XIRR whenever the rental-income account has entries linked to
this property. No Instrument split, no mode toggle.

### Benchmark configuration panel

A settings panel defines which benchmark applies to each asset class. Pre-set
defaults:

| Asset class | Default benchmark | Rationale |
|---|---|---|
| Equity / MF | Auto (large→Nifty 50, mid→Midcap 150, small→Smallcap 250) | Matches instrument market cap |
| FD | CPI (inflation) | "Am I beating inflation?" |
| PPF / EPF | CPI (inflation) | Same |
| Gold | Debt (Nifty Composite Debt Index or equivalent) | Gold is a hedge, compared to safe assets |
| RE | CPI (inflation) | Real estate as inflation hedge |
| Crypto | Nifty Smallcap 250 | Crypto as high-beta risk asset |

Defaults are overrideable per asset class from the panel, and per Instrument
from the position editor (ADR 0015 pattern). Benchmark history is cached from
the market-data provider (ADR 0010) so a setting change does not increase data
pull volume.

## Consequences

- XIRR requires a complete, correctly-classified Cash Flow series; a gap in the ledger produces a wrong number rather than an obviously broken one.
- Per-lot P&L is the companion view that exposes individual entry timing, which XIRR deliberately blends away.
- Sharpe ratio requires a daily portfolio NAV series, which the growth graph already provides. No additional data collection needed.
- The risk-free rate for Sharpe is a daily T-bill yield. If T-bill data is unavailable from the market-data provider, the FD fallback is a separate cacheable series.
- The benchmark config panel is a new UI surface (settings) that populates the Instrument-level benchmark dropdown defaults.
