# One Position shape, differing by Valuation Strategy

Every asset class is a ledger of Transactions over a Position; asset classes differ only in how the Position is *valued* — market-priced, accrual, appraised, or yield-derived — plus their Instrument metadata. Gold and real estate are therefore ordinary ledger-tracked Positions, not special cases, and a fixed deposit is a Position whose value accrues from principal and rate.

## Considered Options

- **Two-tier model** (ledger-tracked vs valuation-only assets): rejected because real estate and gold are genuinely bought on a date at a cost, so excluding them from the ledger discards real information.
- **Per-asset-class models**: rejected because every reporting view would then need per-class logic, and net worth would not compose.

## Consequences

- The Position schema must stay honest: each Instrument kind declares which Transaction types are valid and which Valuation Strategy it uses, rather than one table with nullable columns for every asset class.
- A new asset class should be addable without a schema migration.
