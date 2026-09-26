# Sidecar backup service and forward-only schema migrations

Backups and schema migrations are user-visible concerns the application must
design for from the start (ADR 0012).

## Decisions

### Backup

1. **Backup unit is the single SQLite file.** The user backs up the encrypted
   database; the encryption password is the user's secret, stored separately
   (ADR 0019). Price history inside the database is included by default — it is
   re-fetchable but harmless to carry in a backup.

2. **`db:backup` CLI writes a consistent snapshot.** The command uses
   SQLCipher's `sqlcipher_export()`/`VACUUM INTO` rather than a file copy, so
   it never captures a torn state even with concurrent writers.

3. **Rolling automatic backups are produced by a sidecar container** in
   packaged (Docker) runs only. The sidecar uses the same image with a
   supercronic cron daemon set to a 24-hour interval, sharing `DATA_DIR` and
   `BACKUP_DIR` with the app service. A long-lived resident process is the
   schedule mechanism because docker-compose has no native scheduler. The
   sidecar never runs Alembic.

4. **Pre-migration backups are written by the app entrypoint** before
   `alembic upgrade head`. A marker file (`DATA_DIR/.migration-in-progress`)
   tells the sidecar to skip-and-retry during the migration window.

5. **Two retention classes**:
   - Rolling automatic: keep 5 (`auto-*.sqlite`), pruned oldest-first.
   - Pre-migration: keep 3 (`pre-migrate-<from>-<to>-*.sqlite`), pruned
     oldest-first.
   - Manual backups are never pruned.

6. **`BACKUP_DIR` env** controls where backups are written, defaulting to
   `DATA_DIR/backups/`. Documentation warns that same-volume backups protect
   against migration failure and DB corruption but not against disk or volume
   loss.

7. **Each backup gets a JSON companion file** capturing `kind`, `created_at`,
   schema revision, and app version — used by the restore command and by the
   app's health endpoint to report staleness.

8. **No automatic backups in development** (`mise run dev`). The developer runs
   `mise run db:backup` explicitly.

### Restore

9. **Phase 1 ships `db:restore --from <file>`** that validates the password
   opens the file, reports both schema revisions, refuses to run if the
   application process is live, and swaps the file.

10. **Full "restore latest automatically"** is deferred post-Phase-1.

### Export

11. **Export is defined as JSON (full ledger) + CSV (Transactions, Income)
    but deferred to post-Phase-1.** The DB backup is the Phase 1 data-liberation
    path. Original PDFs cannot be exported (ADR 0019 discards them after
    import).

### Schema migrations

12. **Alembic** (ADR 0018) forward-only. No downgrade scripts.

13. **Automatic on container start**: the image entrypoint runs
    `alembic upgrade head` before starting uvicorn, refusing to serve against
    a stale schema. Development uses the explicit `mise run db:migrate`
    (ADR 0018).

14. **Version guard**: the application starts only if the database revision is
    an ancestor of the code's current revision (i.e. at or before `head`). If
    the database is ahead of the code, the application exits with an error
    naming both revisions.

15. **Failure behaviour**: migrations run in a transaction where possible. On
    failure the function rolls back, exits non-zero, and prints restore
    instructions pointing at the pre-migration backup. It never auto-restores.

### UI indication

16. The frontend footer shows "Last backup" staleness. Market-data staleness
    (ADR 0010) can reuse the same strip later; neither justifies a dedicated
    Settings screen in Phase 1.

## Rationale

- A sidecar separates concerns: backup runs and retention fires regardless of
  app availability, and a container-internal daemon is self-contained within
  the compose file rather than pushing the schedule to host cron.
- Forward-only with a version guard prevents the most common self-hoster
  mistake — pulling the old image after the newer one migrated the DB — from
  being silently destructive.
- Pre-migration backups are the only safety net for a failed migration;
  auto-restore would trade a stopped container for a silently overwritten
  database, which is worse in a personal tool where the user may not notice
  for days.
- Deferring export keeps Phase 1 focused on CAMS import → net worth; the
  backup sidecar already gives the user a self-contained encrypted copy of
  everything.

## Consequences

- The image must ship a `python -m app.cli backup` command that does not
  start uvicorn, shared by both the manual `db:backup` and the sidecar.
- The sidecar image is the same as the app image; the compose file defines
  it as a second service with a different `command:`.
- The entrypoint script must write and remove the migration marker, ensuring
  it is removed even on a failed migration (trap or `finally`).
- `db:restore` must be documented with a "how to get out of a failed start"
  walkthrough, linked from the migration-failure error message.
- The footer's "last backup" reading polls `BACKUP_DIR` on the health
  endpoint; the app does not reach into the sidecar's process.
