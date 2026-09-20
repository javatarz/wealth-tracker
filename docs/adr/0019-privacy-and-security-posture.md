# Original CAMS PDFs discarded after import; SQLite password-protected at rest

## Decisions

1. **Original CAMS PDFs are not stored.** After casparser extracts the
   transaction data, the PDF is discarded. The SQLite database is the
   authoritative store.

2. **Production SQLite file is password-protected** via sqlcipher (or equivalent
   transparent encryption). The development SQLite file is unencrypted so that
   AI coding agents can read and write it freely when operating against the
   development instance (which uses mock CAMS CAS data, never real portfolio
   data).

3. **Nothing leaves the machine except ISIN/AMFI codes** for market-data
   lookups (per ADR 0010). No portfolio data — no position values, no balances,
   no names — is ever sent to an external service.

4. **Documentation must warn** that binding the application to `0.0.0.0`
   or placing it behind a reverse proxy without authentication exposes all
   portfolio data.

5. **Future parser evaluations** must include a criterion: the parser must not
   phone home or send any document data to an external service. casparser has
   already been validated against this criterion.

## Encryption approach

- **Dev mode:** standard SQLite via `sqlite3` module. No encryption key set.
  The `DATA_DIR/.env` or `WEALTH_TRACKER__DB_PASSWORD` env var is absent or
  empty in dev, so the application opens the database without a key.
- **Prod mode:** the application detects a configured password and uses
  `pysqlcipher3` (or equivalent) to open an encrypted SQLite database. The
  password is provided via environment variable, never committed.

## Rationale

- The original PDF is the most sensitive artifact — it contains the full
  statement with every folio, scheme, transaction, and the investor's name,
  address, email, mobile, and PAN. Once the structured data is extracted, the
  PDF is pure liability.
- Password-protecting the SQLite file ensures that even if the host is
  compromised (e.g. a backup lands in the wrong place), the data is not
  trivially readable.
- Dev instances are by design AI-accessible. Mock data means no real user data
  is at risk, and the unencrypted database removes a friction point for
  tooling.

## Consequences

- The PDF-to-JSON extraction is a one-shot pipeline — re-import requires the
  original PDF, which the user must keep independently if they want to re-run
  casparser.
- The application must abstract the database connection behind a factory that
  selects the right driver based on the presence of a password.
- sqlcipher adds a C extension dependency (`libsqlcipher`). The dev
  environment's `pyproject.toml` should make it an optional extra.