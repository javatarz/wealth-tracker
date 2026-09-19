# SQLite now, DuckDB as a later analytics layer

The application stores data in SQLite. The workload is mixed read/write at small scale — a few thousand Transactions per investor lifetime — so a row-oriented engine fits better than an analytics database, and SQLite needs no server for a self-hosted install. If analytical queries later become slow, DuckDB can read the SQLite file directly via its `sqlite` extension, so the analytics layer can be added without migrating data.

## Considered Options

- **DuckDB from day one**: stronger for aggregations, weaker for the row-at-a-time writes that dominate import, and an unfamiliar dependency for no current benefit.
- **PostgreSQL**: a server to run, secure, and back up — the wrong cost for a single-instance personal tool.
