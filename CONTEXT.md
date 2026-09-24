# Wealth Tracker

A privacy-focused, self-hostable tool for tracking an Indian household's wealth over time. It ingests portfolio data (starting with CAMS mutual fund statements), builds a time-series view of holdings, and projects whether the household's Goals will be met.

## Language

### Wealth structure

**Household Member**:
A person whose wealth this instance tracks. The instance may hold several (a couple, their children). Every Account belongs to exactly one Household Member.
_Avoid_: User, person, owner, investor

**Account**:
A container for Positions at one institution: a CAMS folio, a demat account, a PPF account, a fixed deposit. Belongs to exactly one Household Member.
_Avoid_: Wallet, bucket, folio (a folio is one kind of Account)

**Portfolio**:
The complete set of Positions owned by a Household Member, or aggregated across the whole household. Which level is meant is contextual; a Portfolio is always a view over Positions, never a stored grouping.
_Avoid_: Holdings, investments, book

**Net Worth**:
The scalar sum of the current value of every Position in a Portfolio at a point in time.
_Avoid_: Total, valuation, corpus

**Instrument**:
The thing a Position holds: a mutual fund scheme, a stock, gold, an FD product, a property. Shared across Accounts — two Household Members can hold the same Instrument.
_Avoid_: Asset, security, product

**Scheme**:
An Instrument that is a mutual fund plan (e.g. "Parag Parikh Flexi Cap Fund – Direct Growth"). The CAMS-native unit of holding.
_Avoid_: Fund, MF, AMC

### Positions and the ledger

**Position**:
The quantity of one Instrument held within one Account, together with its transaction history. Every Position is ledger-tracked; Positions differ only by Valuation Strategy and Instrument metadata.
_Avoid_: Holding, investment, asset

**Transaction**:
A dated, immutable event against a Position that changes its quantity or cost basis: a purchase, redemption, SIP installment, contribution, or maturity.
_Avoid_: Entry, record, movement, order

**Income**:
Value a Position generates without changing its quantity: a dividend, an IDCW distribution, interest, or rent. Income is either withdrawn or reinvested; reinvested Income produces a Transaction.
_Avoid_: Cash flow, yield, payout, return (Income is one component of return)

**Cash Flow**:
Money crossing the boundary between the household and a Portfolio: a contribution, a redemption, or withdrawn Income. Reinvestment and price movement stay inside the Portfolio and are not Cash Flows.
_Avoid_: Transaction (a Transaction may be internal), movement, transfer

**Lot**:
A parcel of units within a Position acquired in a single Transaction, carrying its own acquisition date and cost basis. Lots are reduced by FIFO or average-cost depending on the reporting need.
_Avoid_: Tax lot, parcel, tranche

**Opening Balance**:
A synthetic Transaction that seeds a Position's starting quantity at a given date, used when no known history exists before that point. Seeded automatically on a first import (ADR 0001). Distinguishable from real Transactions in reporting; never editable or deletable. A mid-history gap uses an Adjustment Transaction instead.
_Avoid_: Startup balance, genesis lot, seed entry

**Adjustment Transaction**:
A Transaction of kind `RECONCILIATION_ADJUSTMENT`, written when "Trust the statement" is chosen for an unexplained mismatch between the statement's printed closing and the derived Position. Dated at the statement's closing date for the delta units, with cost derived from the printed statement's valuation or the period-end NAV. Marked synthetic so reporting can exclude it from real-event counts and P&L attribution.
_Avoid_: Correction entry, fixing row, adjustment (ambiguous)

**Reconciliation Record**:
A non-ledger record created when a mismatch between a statement's printed closing and the derived Position is resolved. Stores the action taken (trusted ledger, trust statement via adjustment, or omitted), the units delta, cost basis (if any), parser version, and timestamp. Surfaced on the Position timeline and the import log. Never affects financial maths.
_Avoid_: Correction log, discrepancy note, audit trail (too broad)

**Valuation Strategy**:
How a Position's current worth is determined. One of **market-priced** (units × price from a feed), **accrual** (principal + rate + elapsed time), **appraised** (user-supplied revaluation), or **yield-derived** (an Income figure capitalised at a rate — a rented property's rent ÷ cap rate).
_Avoid_: Pricing method, valuation type

**Scheduled Transaction**:
A known future flow against a Position: an upcoming SIP installment, an RD contribution, an FD maturity. Feeds both Position tracking and Goal Projection.
_Avoid_: Future transaction, planned transaction, standing instruction

**Benchmark**:
The reference Instrument or index that a Position or asset class is measured against — NIFTY 50 TRI for equity mutual funds, a liquid fund for fixed deposits. Recorded per asset class; a mixed Portfolio uses a blended Benchmark.
_Avoid_: Index, peer, comparable, yardstick

### Goals and projections

**Goal**:
A future financial need with a target amount and a target date: a college fee, a house down payment, a FIRE number, retirement drawdown. Scoped to a Household Member or to the household, and funded from a designated set of Accounts.
_Avoid_: Objective, target, plan, bucket

**Projection**:
A deterministic forecast of whether a Goal will be met, computed by a user-chosen Projection Strategy.
_Avoid_: Simulation, forecast, model

**Projection Strategy**:
A chosen method for estimating future growth: a fixed CAGR, or an average growth rate over a trailing window of *n* years. Users pick between them.
_Avoid_: Assumption, growth rate, return estimate
