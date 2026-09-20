# Income is a first-class ledger event

Dividends, IDCW distributions, interest, and rent are recorded as **Income**
events, separate from Transactions. Income does not change a Position's
quantity and is therefore invisible to a holdings-only model, yet it is part of
total return and is taxable on receipt regardless of reinvestment.

## Disposition

Every Income event carries a `withdrawn` or `reinvested` flag. Withdrawn Income
crosses the boundary between the household and the Portfolio and counts as a
Cash Flow for XIRR. Reinvested Income does not — treating it as fresh money
would understate returns.

A reinvested Income event produces a corresponding Transaction that increases
the Position's quantity. For CAS-sourced IDCW reinvestments the link is
automatic (both sides derive from the same statement line), and the generated
Transaction carries a FK back to the Income event. For manually-entered
reinvested Income the FK is optional.

## Source per kind

| Kind | Source | Income event? |
|------|--------|---------------|
| MF IDCW | CAS statement via casparser (auto) | Yes |
| Stock dividend | Manual entry | Yes |
| FD/PPF/EPF interest | Internal to accrual valuation only | **No** |
| Rent | Manual entry | Yes |

Accrual instruments (FD, PPF, EPF) do not produce Income events. Their
interest is computed inside the accrual valuation formula
(`principal × rate × elapsed / 365`) and reported as a stated rate. Multi-year
FDs show CAGR in a secondary slot.

## Stock dividends

Broker P&L reports aggregate dividend payouts per account but do not attribute
them per stock. Stock dividends are therefore entered manually. For projection
they are extrapolated via a dividend yield applied to the position value.

## Cash flow series

Withdrawn Income enters the XIRR cash flow series at the Income event's
economic date — NAV date for CAS-sourced events, user-entered date for manual
events, not the pay date.

## Scope

Income is tracked per Position. A household-level Income view is a live
aggregation of Position Income — no separate household Income entity.

## Identity and de-duplication

Income events are identified by content hash over
`(instrument_id, date, amount, disposition, kind)`, following the same pattern
as the Transaction content-hash scheme (ADR 0006).

## Consequences

- The disposition flag is load-bearing rather than cosmetic — getting it wrong
  misstates XIRR.
- Rent, dividends, and interest share one representation, so the projection
  engine can consume them uniformly.
- Accrual-interest non-events mean less bookkeeping and no de-duplication work
  on reimport, at the cost of not surfacing accrual interest as line items.
- Dividend projection requires yield assumptions, which are inherently
  uncertain — the UI should flag projected dividends as estimates.
- Manual stock-dividend entry is a data-quality risk (user may skip it);
  future integration with corporate-action data feeds could reduce this.
- FK linkage on CAS-sourced reinvestments is automatic and reliable; on manual
  entries it is optional and may be absent.