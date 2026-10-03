# Goal funding and projection mechanics

A Goal is a forward-looking scenario: "I want ₹X by date Y, funded from my
portfolio with a specified asset-class mix." Goals are projected deterministically
(ADR 0009) with per-asset-class growth rates.

## Goal model

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | User-facing label |
| `target_amount` | decimal | Nominal or real (see below) |
| `target_date` | date | When the corpus is needed |
| `target_is_real` | boolean | `true` = today's money (engine inflates to nominal) |
| `inflation_rate_override` | decimal | Override default CPI per Goal (e.g., 10% for education) |
| `priority` | integer | Lower = higher priority. Default by earliest target_date |
| `funding_mix` | map[asset_class → percentage] | Sums to 100%. Defines the asset-class composition of the Goal's projected corpus |

### Target amount: nominal vs real

The user can specify targets in either mode:

- **Real** (`target_is_real = true`): the amount in today's purchasing power.
  The engine inflates it to the target date using the applicable inflation rate
  to get the nominal target. Show both numbers.
- **Nominal** (`target_is_real = false`): the amount is used as-is at the
  target date. No inflation applied.

### Inflation

| Use | Default | Source |
|-----|---------|--------|
| General CPI | Latest MoSPI CPI | MoSPI eSankhyiki API (free, JSON, monthly) |
| Education inflation | 10% | Industry consensus; CPI Education sub-index (~3.5%) understates private costs |
| Fallback (general) | FRED / World Bank | If MoSPI unreachable |

The inflation rate is user-overrideable per Goal.

### Default priority

Goals are ordered by earliest `target_date` ascending. User can reorder by
editing the `priority` field.

## Funding mix

The `funding_mix` defines the asset-class composition of the Goal's projected
corpus. Each key is an asset class; values are percentages summing to 100%.

When the user sets the mix, the engine validates that each asset-class bucket
can be satisfied by the projected portfolio at the goal date (post-payout of
higher-priority Goals). If a bucket is underfilled, the system flags it and
the user can adjust the mix or increase contributions.

### Projection mechanics per asset class

1. The engine groups all Positions by asset class.
2. Scheduled Transactions are allocated to their Instrument's asset class.
3. Each asset class grows at its assumed rate (per-asset-class CAGR, from the
   projection strategy).
4. At a Goal's target date, the allocated value is withdrawn from the
   portfolio. Lower-priority Goals project from the residual (reduced
   compounding).

This is a liability-driven model: higher-priority Goals are funded first, and
lower-priority Goals see the reduced pool.

## Income surplus constraint

A monthly investable surplus (income − expenses) caps total Scheduled
Transaction contributions across all Goals.

| Parameter | How it works |
|-----------|-------------|
| Base surplus | User sets a monthly amount (₹) |
| Growth schedule | Piecewise by age range. Defaults below, all editable |
| Negatives allowed | Surplus can decline (negative growth) in later years |

### Default surplus growth rates

Based on industry data for Indian tech professionals (publicly reported in
Michael Page, LinkedIn, Naukri, AmbitionBox salary surveys).

| Age range | Default annual growth | Rationale |
|-----------|----------------------|-----------|
| 22–30 | 10% | Career acceleration + job-hop bumps (20–30%). Surplus grows faster than salary since base expenses lag income growth. |
| 30–40 | 8% | Senior IC / EM tier. Promotions slow, absolute increments larger. |
| 40–50 | 5% | Leadership / principal track. Plateaus. |
| 50+ | 3% | Pre-retirement. Growth tapers. |

The age ranges and rates are fully editable in the UI — the user can drag range
boundaries and change any rate. Defaults are labelled as "based on industry
data for tech professionals."

### Surplus allocation among Goals

Priority fill: the highest-priority Goal gets its required monthly contribution
first. The next Goal gets the residual, and so on. If surplus cannot cover all
Goals, each shortfall is displayed per Goal.

## Goal-driven Scheduled Transactions

Existing Scheduled Transactions auto-count toward Goals through their
Instrument's asset class. If the projection shows a gap, the Goal UI offers to
create a new Scheduled Transaction to close it. New Transactions are created
from the Goal view with a single action.

Scheduled Transactions are managed from a dedicated UI (click through from
asset class). Increasing a SIP updates the projection in real time.

## Goal lifecycle

| Event | Behavior |
|-------|----------|
| On track (projected ≥ target) | Green status. No auto-action. |
| At risk (projected < target) | Amber/red status with gap amount. |
| Target date passes | Archived and labelled "met" or "missed." |
| Mid-course change | Projection recomputes. New gap flagged. Existing Goal-linked Scheduled Transactions adjust or show updated gap. |

## Progress display

Three-number bar per Goal:

```
Current allocated  |  Projected at goal date  |  Target (inflated)
```

Color: green if projected ≥ target, amber if ≥ 80%, red otherwise.

## Relationship to existing ADRs

| ADR | Relationship |
|-----|-------------|
| 0009 | Deterministic projection method — Goal projections use it |
| 0022 | Scheduled Transactions with escalation feed into Goal projections |
| 0004 | Per-asset-class growth rates from the benchmarks table |
| 0003 | Income events enter the surplus model indirectly (income − expenses) |
| 0016 | Position valuations computed from price history feed the projection |

## Consequences

- The surplus model is an approximation — it assumes the user knows their
  investable surplus and updates it when circumstances change.
- Age-range growth rates are a guess, not a guarantee. The UI must not imply
  certainty.
- Priority fill is simple but can leave lower-priority Goals stranded if the
  user doesn't regularly review them.
- Linking Goals to asset classes rather than accounts avoids administrative
  overhead but makes the projection dependent on the engine's asset-class
  classification being correct.
- The liability-driven funding flow (withdrawal at goal date reducing residual
  compounding) is more computationally intensive than independent Goal
  projections.
