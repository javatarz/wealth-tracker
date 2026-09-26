# Mismatches are resolved by decision cards with three write semantics

A mismatch between a statement's printed closing units and the ledger's derived Position is surfaced as a decision card bearing three mutually exclusive actions. Each resolves the mismatch — the import cannot complete until every card is acknowledged — but only one action writes a ledger row.

**Trust our ledger** writes nothing. The derived Position stands; a reconciliation record stores the delta and the decision, so a later reader sees the discontinuity was deliberate.

**Trust the statement** writes a `RECONCILIATION_ADJUSTMENT` Transaction for Δ units dated at the statement's closing date. Cost basis is derived from the statement's printed `valuation.cost` when present, else Δ × the period-end NAV. The row is marked synthetic so reporting can distinguish it from real Transactions. This action is for the *unexplained* gap — no single imported row accounts for Δ. When a culprit row exists (misclassified, misparsed), the user should resolve it through the UNKNOWN row's own card, which writes a real Transaction and needs no adjustment.

**Leave this Scheme out** writes nothing to the ledger and skips this Scheme's rows entirely for this statement. The Account (folio) is not created if the omitted Scheme was its sole holding. Prior imports are untouched — the ledger is immutable, and overlapping rows from earlier statements stay. The omission is recorded as a reconciliation decision.

All three produce a **reconciliation record** holding: scheme, import, action, statement closing units, derived units, Δ, cost basis (where applicable), parser version, and timestamp. These records are surfaced on the Position timeline and the import log. They never affect financial maths.

The "Book the difference as an opening balance" action is not offered on a mismatch card. Opening balances (ADR 0001) remain reserved for first-import anchoring — the case where the Position has no known history at or before the statement's first point. A mid-history gap uses the `RECONCILIATION_ADJUSTMENT` instead; an opening balance inserted mid-history would fabricate a lot at the wrong date and cost, corrupting per-lot P&L and XIRR.

Supersession — correcting an already-committed wrong row by voiding it and inserting a replacement — is a general ledger capability that applies beyond reconciliation. Its design is deferred. This ticket flags it as a future concern.

## Considered Options

- **Opening balance for mid-history gaps**: rejected — misdates and miscosts the gap, corrupting per-lot P&L and XIRR. Opening balances semantically assert "history begins here," which is incoherent on a Position with preceding transactions.
- **"Flag for later" fourth button**: rejected — the user can re-import the same statement to revisit a mismatch; a separate "needs attention" surface adds complexity without a clear benefit.
- **Adjustment dated before the oldest transaction**: considered and rejected during grilling — dating the gap at the statement's closing period end is simpler and makes fewer claims about the gap's origin.
- **Blind correction without cost basis**: rejected — without a cost basis the Position would carry units with zero cost, breaking P&L and XIRR. Cost is always derived from the best available source (printed then NAV).

## Consequences

- ADR 0001 is narrowed: opening balances are only for Positions with no known history at or before the first known statement period. Mid-history gaps use `RECONCILIATION_ADJUSTMENT`.
- ADR 0006's content-hash dedup must be overrideable for re-imports (the revisit path for a previously omitted or acknowledged-but-deferred mismatch).
- The Transaction type enum gains `RECONCILIATION_ADJUSTMENT`. A `synthetic` boolean distinguishes it from real rows.
- A `reconciliation_decisions` table is added (one row per mismatch per import), linked to `Import` (the batch) and `Position`. Never affects financial computation.
- ADR 0019's PDF-discard policy means re-importing requires the user to regenerate or retrieve the original file — we store parsed rows but not the PDF.
- The fixture PDF (ADR 0020) should include a scenario that exercises the reconciliation-adjustment path.
