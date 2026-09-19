# Benchmarks are assigned per asset class by shipped defaults, overrideable per Instrument, blended by summing independent series

Every growth graph carries a Benchmark. Benchmarks are assigned by asset class
(optionally overridden per Instrument), and a mixed Portfolio's blended Benchmark is
the sum of each component's benchmark series starting from its own investment amount.

## Default benchmarks per asset class

Shipped with the product, overrideable per Instrument:

| Asset class | Default Benchmark | Rationale |
|-------------|-------------------|-----------|
| Equity MF (large-cap) | NIFTY 50 TRI | Standard large-cap index |
| Equity MF (mid-cap) | NIFTY Midcap 150 TRI | Category-appropriate |
| Equity MF (small-cap) | NIFTY Smallcap 250 TRI | Category-appropriate |
| Equity MF (other / unspecified) | NIFTY 50 TRI | Sensible default; user overrides per Instrument |
| Equities (direct stocks) | NIFTY 50 TRI (or category-specific TRI per market-cap) | Same logic as MFs |
| Gold (ETF and physical) | FD rate (e.g. 3-month / 1-year SBI FD) | Most natural alt-investment comparison |
| Crypto | NIFTY Smallcap 250 TRI | Peer in volatility / risk profile |
| FD | Inflation (CPI) | Real-return comparison |
| Property | FD rate | Opportunity-cost comparison |
| PPF | (none) | Fixed return; no market series to compare against |

The user can override any Instrument's benchmark at creation or edit time by choosing
a different Instrument or index from the same pool.

## Blended benchmark

A Portfolio holding multiple asset classes gets a blended Benchmark computed as the sum
of independent benchmark series:

    blended(date) = Σ benchmark_series(position, date)

Each benchmark series starts at the position's investment amount and grows independently
from that baseline. For a lump-sum investment of ₹6L in Asset A benchmarked against
NIFTY 50 TRI:

    series(date) = 600000 × (NIFTY_TRI(date) / NIFTY_TRI(initial_date))

For SIP contributions, each contribution adds its own increment to the series from its
own contribution date. The blended Benchmark is therefore a running sum of independent
lines, each growing at its benchmark's rate — exactly matching the portfolio's own
composition drift without any rebalancing assumption.

This means the blended Benchmark line produces an absolute value directly comparable
to the Portfolio's own absolute value. The delta between the two lines is the `₹`
outperformance or underperformance.

## Presentation

The Benchmark line is **rebased** to the Portfolio's starting value (or to the start of
the displayed date range). Both lines start at the same point, making the delta readable
as currency outperformance/underperformance without mental arithmetic.

## Overrideability

Instrument-level only. Setting an Instrument's benchmark overrides the asset-class
default for that Instrument alone. Account-level overrides are not supported — if the
same override pattern repeats across multiple Instruments, the asset-class default
should be changed.

## Consequences

- A new asset class added later gets a shipped default; existing Instruments in that
  class inherit it after a migration.
- The blended Benchmark computation is stateful: it must track each Position's
  contributions and their dates to know which benchmark increment to add. This is the
  same data XIRR already needs (ADR 0004), so no new ledger query is required.
- Inflation as a Benchmark requires a CPI series source, which is not an existing data
  provider (ADR 0014 covers markets, not economics). A placeholder or hard-coded annual
  rate may be needed until the source is identified.