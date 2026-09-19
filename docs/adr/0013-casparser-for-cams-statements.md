# CAMS statements are parsed with casparser, pinned and local-only

CAMS and KFintech consolidated account statements are parsed with [casparser](https://github.com/codereverser/casparser) (MIT), pinned to an exact version. Its dependency set contains no HTTP client, so the parse path cannot transmit statement contents — the requirement set by ADR 0007 and ADR 0010. It exposes a per-folio, per-scheme, per-transaction model with JSON Schemas, and `CASData.parse_warnings` reconciles each scheme's transactions against the statement's own printed running unit balance.

## Considered Options

- **`cas2json`** (AGPL-3.0, PyMuPDF): a workable fallback, but its PDF engine is AGPL unless a commercial licence is bought, the repository has no test suite, and its NSDL/CDSL support is self-declared BETA. Held back as a per-file fallback only.
- **Hosted parsing APIs** (`casparser.in` and similar): disqualified outright — the statement leaves the machine.
- **`processcaspdf`, `mutualfund-stmts-etl`, `saransh-workflows`, `CAMSPdfExtractor`**: rejected on maintenance record, field coverage, or an HTTP call on every run.

## Consequences

- casparser parses only **original, issuer-delivered consolidated** CAS files. Re-prints, browser "Save as PDF", broker-reformatted files, MFCentral statements and single-AMC statements all fail by design. Each is a distinct user-facing error path, not a bug.
- Per-transaction cost basis and average price are **not printed in the statement**. They must be derived at import and labelled as derived.
- The ISIN database ships pinned. `casparser-isin --update` contacts the author's server, so automatic update is off by default.
- The parser version must be recorded against each imported statement, because parser output changes additively between minor releases.
