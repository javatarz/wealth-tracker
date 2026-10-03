# Wealth Tracker

[![Status: Phase 1](https://img.shields.io/badge/status-Phase_1-blue)](#)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![Stack: Python/FastAPI](https://img.shields.io/badge/stack-Python%2FFastAPI-3776AB?logo=python&logoColor=white)](docs/adr/0011-stack.md)
[![Stack: TypeScript/React](https://img.shields.io/badge/stack-TypeScript%2FReact-3178C6?logo=typescript&logoColor=white)](docs/adr/0011-stack.md)
[![PRs: welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](#)

A privacy-focused, self-hostable tool for tracking an Indian household's wealth over time. Ingests portfolio data (starting with CAMS mutual fund statements), builds a time-series view of holdings, and projects whether Goals will be met.

## Status

**Phase 1 — Foundation.** The domain model, architecture decisions, and design prototypes are in place. Implementation is underway.

- [Project map](https://github.com/javatarz/wealth-tracker/issues/1) — tracker of record for all work.
- [Glossary](CONTEXT.md) — ubiquitous language (shared across agents and conversation).
- [Architecture decisions](docs/adr/) — settled design in ADRs.
- [Prototypes](prototypes/) — throwaway HTML prototypes exploring UX.

## Stack

| Layer | Choice |
|-------|--------|
| Backend | Python, FastAPI, SQLite (`sqlite3`), Alembic |
| Frontend | TypeScript, React, Vite |
| Toolchain | [`mise`](https://mise.jdx.dev) — pins Python/Node, runs dev/test/lint tasks |
| Runtime | Docker (single image, SQLite on a mounted volume) |
| Testing | pytest, Vitest, Playwright, ruff, mypy, ESLint |

All per [ADR 0011](docs/adr/0011-stack.md) / [ADR 0012](docs/adr/0012-mise-and-docker.md) / [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md) / [ADR 0026](docs/adr/0026-strict-toolchain-guardrails.md).

## Quick Start

Requires [`mise`](https://mise.jdx.dev/getting-started.html). It installs the pinned Python, Node, uv and pre-commit for you.

```bash
mise run setup   # once: toolchain, dependencies, git hooks, database
mise run dev     # app with hot reload at http://localhost:5173
```

The page shows the backend's `/api/health` status.

Every command is a mise task. `mise tasks` lists them all:

| Command | What it does |
|---------|--------------|
| `mise run dev` | Migrate the database, then run uvicorn (`:8000`) and Vite (`:5173`) with hot reload |
| `mise run test` | Backend (pytest) and frontend (Vitest) tests |
| `mise run lint` | Lint and format-check both sides |
| `mise run format` | Auto-fix lint and formatting |
| `mise run typecheck` | `mypy --strict` and `tsc` |
| `mise run check` | Full gate, same as CI: OpenAPI drift, all hooks, tests |
| `mise run openapi` | Regenerate the OpenAPI spec and frontend types after changing API models |
| `mise run db:migrate` | `alembic upgrade head` |
| `mise run start` | Packaged app in Docker at http://localhost:8000 (see [Docker](#docker)) |
| `mise run build` | Build the Docker image |
| `mise run fixtures:cams` | Regenerate the synthetic CAMS CAS PDF in `tests/fixtures/` |

Git hooks run automatically after setup: lint, format and type checks on every commit, and tests plus the OpenAPI drift check on every push.

Configure via environment variables (see [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md)).

## Docker

Requires Docker with the Compose plugin. No Python or Node install needed.

```bash
mise run start              # or, without mise: docker compose up --build
```

Open http://localhost:8000. One container serves both the API and the compiled frontend, and runs `alembic upgrade head` before starting.

- **Data** lives in the `data` named volume, mounted at `/data` (SQLite at `/data/wealth.db`). It survives `docker compose down` and image rebuilds; `docker compose down -v` deletes it.
- **Config** via environment variables, e.g. `PORT=9000 LOG_LEVEL=debug mise run start`:

  | Variable | Default | Purpose |
  |----------|---------|---------|
  | `PORT` | `8000` | Port uvicorn listens on, published on the host |
  | `LOG_LEVEL` | `info` | `critical`, `error`, `warning`, `info` or `debug` |
  | `DATA_DIR` | `/data` | SQLite location inside the container |

> **Security:** the app has no authentication ([ADR 0007](docs/adr/0007-no-authentication.md)). `docker-compose.yml` publishes the port on `127.0.0.1` only. Binding it to `0.0.0.0`, or putting it behind a reverse proxy without authentication, exposes all portfolio data to anyone who can reach it ([ADR 0019](docs/adr/0019-privacy-and-security-posture.md)).

## What's Runnable Today

- The app skeleton via `mise run dev` (see Quick Start) or `mise run start` (see Docker)
- `mise run fixtures:cams` — generates the synthetic CAMS CAS PDF used in tests
- Open `prototypes/cams-import/index.html` and `prototypes/screens-nav/index.html` in a browser to explore the UI design concepts

## Documentation

- **[CONTEXT.md](CONTEXT.md)** — glossary and domain language
- **[docs/adr/](docs/adr/)** — architecture decision records covering the full design
- **[docs/research/](docs/research/)** — research on third-party data sources and formats
- **[AGENTS.md](AGENTS.md)** — conventions for AI agents working on this repo

## License

[AGPL-3.0](LICENSE) — see the `LICENSE` file for the full text.
