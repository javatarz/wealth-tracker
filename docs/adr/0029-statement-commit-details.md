# How a committed statement becomes ledger rows

Committing an import (#26) turns a parsed CAMS/KFintech statement into Accounts,
Instruments, Positions, Transactions and Lots in one database transaction. A
few details were not settled by earlier ADRs.

## Decisions

1. **The commit re-parses the PDF.** The browser sends the same file (and
   password) it previewed, not the preview JSON, so the server never trusts
   client-edited figures. The PDF's SHA-256 is stored on the `Import`; the PDF
   itself is discarded as before (ADR 0019). A second commit of the same file
   is rejected with `409 already_imported`.

2. **Transaction fingerprints count repeats.** ADR 0006's fingerprint covers
   date, Account, Instrument, type, units and amount. Two genuinely identical
   rows in one statement (two same-day SIPs of the same amount) would collide,
   so the fingerprint also includes the row's occurrence number among identical
   rows in that statement. An overlapping statement carrying the same rows
   produces the same occurrence numbers and is skipped.

3. **Instrument identity falls back when AMFI is missing.** ADR 0015 identifies
   a mutual fund by AMFI code. Some statements omit it; those schemes fall back
   to ISIN, then to `<rta>:<rta_code>`. Reconciling a fallback identity to its
   AMFI code later is a data fix, not a schema change.

4. **Opening Balance cost is priced at the first NAV in the statement.** When a
   first import finds non-zero opening units (ADR 0001), the synthetic
   `OPENING_BALANCE` Transaction is dated at the statement's start and costed at
   the opening units × the NAV of the earliest priced row (or the closing NAV if
   there are none). CAMS does not print the opening cost, so this is an estimate,
   flagged by `synthetic`.

5. **Every statement row is kept**, including zero-unit `UNKNOWN` rows such as
   IDCW payouts and "(Adjustment)" lines, because the PDF is not retained and
   reconciliation (#27) and Income (#35) need them. Lots change only for rows
   with non-zero units: positive units open a Lot, negative units reduce Lots
   FIFO.

6. **Decimals are stored as text** so SQLite never rounds money or units
   through a float.

## Consequences

- A statement imported out of order (an older period after a newer one) still
  dedups, but its disposals are applied to the Lots present at commit time, so
  FIFO cost basis can drift. Reconciliation (#27) is where that surfaces.
- Changing the fingerprint inputs changes every fingerprint;
  `FINGERPRINT_VERSION` must be bumped with it.
