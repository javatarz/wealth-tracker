# How mismatch decisions travel through an import commit

ADR 0027 settled what each decision-card action writes. This records how the
commit flow (#27) collects those decisions and the details 0027 left open.

## Decisions

1. **Detect before writing.** For every Scheme the commit first plans what it
   would add: the ledger's units up to the statement's closing date, an Opening
   Balance if the Position has no history by then, and the statement rows whose
   fingerprints aren't already in the ledger. Derived units are the sum of those.
   A Scheme is mismatched when that differs from its printed closing units. The
   same plan is then written, so detection and writing can't disagree.

2. **Stateless two-step commit.** `POST /api/imports` answers
   `{"outcome": "needs_decisions", "mismatches": [...]}` and writes nothing while
   any mismatch lacks an Action. The client posts the same PDF again with a
   `decisions` form field (JSON, holding key → `trust_ledger` |
   `trust_statement` | `leave_out`). Nothing is held server-side between the two
   calls, so an abandoned review leaves no trace. A completed commit answers
   `{"outcome": "committed", ...}`. Both outcomes are 200; errors keep their
   status codes.

3. **Decisions are keyed by holding**, `institution|folio|instrument identity`,
   the same key Transaction fingerprints use. Decisions for holdings that turn
   out not to be mismatched are ignored.

4. **Re-importing the same PDF continues its Import.** Content-hash dedup (ADR
   0006) only rejects a repeat when nothing in it is mismatched any more.
   Otherwise the commit adds rows and decisions to the existing `Import` instead
   of creating a second one with the same hash. A Scheme that was trusted to the
   ledger or left out shows its card again. One fixed by Trust-the-statement
   reconciles, so it doesn't.

5. **Adjustment cost.** For a positive Δ, the adjustment's Lot costs the
   statement's printed `valuation.cost` minus the Position's current cost basis.
   If the printed cost is absent, or that difference isn't positive, it costs
   Δ × the closing NAV. A negative Δ reduces Lots FIFO like a redemption, and its
   decision record carries no cost basis.

## Consequences

- The client sends the PDF twice for a mismatched statement. It is parsed
  twice, still never stored.
- The commit endpoint now returns 200 instead of 201.
- The mock fixture PDF still reconciles. Mismatch tests shift the parsed
  closing units instead of using a second fixture PDF (ADR 0027 asks for one;
  still to do).
