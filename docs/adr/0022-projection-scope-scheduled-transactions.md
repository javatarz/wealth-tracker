# Projection scope: scheduled transactions and escalation

## Decision

Goal projections include the full set of expected future cash flows, not just
the current portfolio. This means the projection engine models:

1. **All existing Positions** at their current market value.
2. **All Scheduled Transactions** — recurring contributions (SIPs, monthly
   EPF/NPS contributions, RD deposits), recurring withdrawals (pension
   payments, SWP), and one-off future events (FD maturity reinvestment, loan
   closure). The user defines these as Scheduled Transactions linked to an
   Instrument.
3. **An annual escalation rate per Scheduled Transaction** that models
   growth (or decline) in the contribution or withdrawal amount over time.

## Escalation rate

The escalation rate is an integer percentage per year, positive or negative.
A +10% rate on a ₹10,000 monthly SIP means year 2 contributions are ₹11,000,
year 3 ₹12,100, etc. A −2% rate models decreasing contributions (e.g.,
reducing EPF top-ups as retirement approaches).

The rate is per Scheduled Transaction, not per Instrument. Two SIPs into the
same fund can have different escalation rates.

## Deferred

A decay schedule on the escalation rate itself (e.g., escalate at 10% for
10 years, then 5% for 10 years, then 0%) is deferred until users ask for it.
A single flat rate (±) is sufficient for v1.

## Relationship to ADR 0009

ADR 0009 decides the *method* (deterministic vs Monte Carlo). This ADR decides
the *scope* — what cash flows the method operates on. They are independent:
both deterministic and Monte Carlo projections include scheduled transactions
with escalation.

## Consequences

- The projection engine depends on Scheduled Transaction data, which is
  optional. A position with no schedule attached is projected flat at current
  value × growth rate.
- The escalation rate compounds yearly, which matches salary-hike patterns.
  Monthly compounding would produce a slightly different number; document the
  convention in the UI.
- Changing a Scheduled Transaction or its escalation rate changes every
  projection that includes it. No data migration needed — projections are
  computed on-the-fly.