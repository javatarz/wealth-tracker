# Position valuations are computed on demand from per-Instrument price history

Every Position's value on any past date is derived as units-on-date × price-on-date, where
price history is stored per Instrument — once, not once per Position holding it. No
valuation records are materialised.

## Storage model

Price history lives in a single `price` table keyed by `(instrument_id, date)`, with a
decimal `price` column and a `source` tag identifying the feed that supplied it. A
Position's value at any point in time is computed:

    valuation(position, date) = units(position, date) × price(instrument, date)

Units on a given date are derived from the Transaction ledger (ADR 0001). Price on a given
date comes from the closest available record at or before that date — the same carry-forward
logic that handles weekends and holidays.

This is the middle ground among three candidates:

| Option | Description | Rejected because |
|--------|-------------|------------------|
| Materialised daily valuations | Store one row per Position per day | Duplicates what can be derived; two Positions holding the same Instrument store the same price twice; derived-table drift between ledger and valuation table |
| Price history, compute on demand | Store price per Instrument per day; derive valuation | — (chosen) |
| Periodic marks only | Store valuation only when a statement or manual mark arrives | Insufficient resolution for XIRR (ADR 0004); re-slicing by date or dimension requires interpolation |

## Granularity

Daily, always. Every data source (AMFI daily NAV, NSE EOD bhavcopy) publishes at daily
frequency. Weekly or coarser would lose information for SIP-driven portfolios where
contributions fall on arbitrary dates. Aggregating to weekly or monthly for display is a
query concern, not a storage concern.

## Valuation Strategies

ADR 0002 established four strategies. The mapping to asset classes is:

- **market-priced** (`units × price` from a feed): mutual funds, equities, ETFs, gold ETFs,
  crypto. Price source per Instrument kind is settled in ADR 0014.
- **accrual** (`principal + rate × elapsed / 365`): fixed deposits, PPF, bonds held to
  maturity. No external price feed; the Position's own terms determine value at any date.
- **appraised** (user-supplied revaluation mark): physical gold, property. The user marks
  to model on their own schedule; between marks the last appraised value is carried forward.
- **yield-derived** (annual Income / cap rate): rented property only, and only when the
  user has set up an Income record and explicitly chooses this strategy. A stretch case;
  not needed for Phase 1.

An Instrument's `valuation_strategy` column (established in ADR 0015) selects the strategy
at query time. Each strategy maps to a different computation, but all accept the same
inputs: a date, the Position's ledger, and the Instrument's price or terms.

## Boundary of the valuation series

A Position valued on a date before its earliest Transaction or opening balance has no known
units. The chart starts at the Position's first known point — the date of its earliest
Transaction or opening balance — and shows nothing before it. No extrapolation or zero line.

## Price gaps

- **Weekends and holidays**: carry forward the last available price. NAV does not change on
  non-business days; equity exchanges have no session. This is automatic: the "closest
  available record at or before date" rule produces the carry-forward behaviour.
- **Suspended schemes**: the last known NAV is carried forward, and the valuation is
  labelled with a staleness indicator so the user can distinguish "priced today" from "last
  priced N days ago".
- **Liquidated or merged schemes**: the Position is closed at the Account level (ADR 0015
  close + reopen pattern), and the price series is frozen at the last available price on
  the closure date.

## Consequences

- The `price` table is append-only and shared across all Positions holding the same
  Instrument. No per-Position valuation data needs to be generated or refreshed.
- Adding a new statement import does not require recomputing or appending to any valuation
  table — the existing price history and the updated ledger produce the correct series.
- A query that asks "Portfolio net worth on every day in 2024" must join the `price` table
  with every Position's ledger. For large portfolios over long time ranges, this may need
  an indexed materialised view. That is a query-tuning concern, not a data-model concern.
- The staleness indicator on suspended schemes requires tracking the last refresh date per
  Instrument kind (ADR 0010's "last updated" timestamp).
