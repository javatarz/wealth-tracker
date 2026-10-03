# Manual entry flows for non-CAMS asset classes

## Decisions

### Indian stocks — broker import primary, manual fallback

1. **Broker import is the primary path.** The user imports their tradebook CSV
   from the broker. The system parses every row and creates one Transaction per
   trade. Without the full trade history, cost basis, lot-level P&L, and
   projections cannot be computed. No "opening balance" shortcut for broker
   import — it would produce a worthless position.

2. **Manual entry is a fallback** for holdings the broker doesn't cover or
   pre-broker-history trades. It supports both opening balance (one bulk lot at
   average cost) and per-trade entry.

3. **Tradebook CSV formats vary per broker** (Zerodha, Groww, Angel One, Upstox
   all use different columns, delimiters, and preamble rows). The application
   needs per-broker import adapters. Details recorded in
   `docs/research/broker-tradebook-formats.md`.

4. **Tradebooks do not contain brokerage or taxes.** Those figures come from
   separate contract notes or P&L reports. The importer records gross trade
   values; costs are added at a reconciliation step.

### Fixed deposits

Single Instrument created with principal, rate, start and maturity dates.
Valuation is accrual — no transaction ledger beyond open/close. Opening balance
mode and detailed mode produce the same Instrument; opening mode skips the
accrual history and records current state plus terms.

### PPF

Annual interest rate is recorded alongside the deposit because the rate
influences accrual. The rate is pre-filled from the current government rate
(e.g. 7.1% as of Apr 2025) but user-overrideable. Deposit amount and date are
recorded for proper interest computation (interest is calculated on the minimum
balance between the 5th and last day of each month).

Opening balance mode: snapshot of current balance plus year opened. Detailed
mode: each annual deposit recorded separately.

### EPF

Opening balance mode captures the current balance, the current monthly
contribution (employee + employer), and an **annual escalation rate** that
models salary/investment growth for projections. This escalation rate is a
general concept that applies to any periodic investment (EPF, NPS, PPF step-up,
SIPs) — it is modelled once in the projection engine, not per-asset-class.

Detailed mode: individual monthly contributions.

### NPS

Same structure as EPF: monthly contribution with an annual escalation rate.
Contributions are allocated across equity, corporate bonds, and government
securities at user-chosen percentages. Valuation is market-priced (NAV-based,
like mutual funds) — the allocation determines which sub-scheme NAVs apply.

### Physical gold

Tracked by weight in grams. Market value = grams × 24K gold spot price × purity
factor. Purchases include making charges (sunk cost — not recoverable in
valuation). Opening balance mode: single bulk lot at average cost per gram.
Detailed mode: each purchase as a separate lot.

### Real estate — two valuation methods

1. **Owned (appraised):** Cost basis = purchase price + stamp duty + registration
   + capital improvements. Value from periodic user-entered appraisal. Rent
   tracked as a separate Income event linked to the Instrument.

2. **Rented (yield-based):** Value = Annual rent ÷ Area rental yield. The yield
   is looked up or entered by the user (typical metro range 2-4%). The rent
   itself is the market signal — no appraisal needed. Cost basis is still
   recorded for P&L computation.

### Crypto

Coin selected from a dropdown (populated from CoinGecko). Current price
automatically looked up. Trade-by-trade entry identical to equities (buy/sell,
quantity, price, exchange fee). Same FIFO lot-matching for sells.

## Prototype

A throwaway HTML prototype explored all eight asset classes with two entry
modes (opening balance vs detailed). Deleted after the decisions were captured
in this ADR (projects use trunk-based development — prototypes live on main
and are removed when the card is closed).

## Consequences

- Per-broker import adapters are needed for each supported broker (Zerodha
  first, then Groww, Angel One, Upstox).
- The tradebook parser must handle varying column names, preamble rows, and
  date formats across brokers.
- Brokerage/taxes must be added at a separate step after the tradebook is
  parsed — the tradebook itself does not contain them.
- The escalation-rate concept is designed once in the projection engine and
  reused across EPF, NPS, PPF, and any future SIP-like periodic investment.
- Real estate rental-yield data can be seeded with metro-level defaults but
  must be overrideable per location.
