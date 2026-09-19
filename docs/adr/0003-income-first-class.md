# Income is a first-class ledger event

Dividends, IDCW distributions, interest, and rent are recorded as **Income** events, separate from Transactions. Income does not change a Position's quantity and is therefore invisible to a holdings-only model, yet it is part of total return and is taxable on receipt regardless of reinvestment. Each Income event records whether it was withdrawn or reinvested, and a reinvested Income produces a corresponding Transaction.

## Consequences

- Only money crossing the boundary between the household and the Portfolio counts as a Cash Flow for return calculations. Treating a reinvested distribution as fresh money would understate returns, so the disposition flag is load-bearing rather than cosmetic.
- Rent, dividends, and interest share one representation, so the projection engine can consume them uniformly.
