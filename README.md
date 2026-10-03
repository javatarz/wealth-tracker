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
| Testing | pytest, Vitest, Playwright, ruff, pyright, ESLint |

All per [ADR 0011](docs/adr/0011-stack.md) / [ADR 0012](docs/adr/0012-mise-and-docker.md) / [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md).

## Quick Start

Requires [`mise`](https://mise.jdx.dev/getting-started.html).

```bash
mise install        # Install pinned Python, Node, uv, pre-commit
mise run install    # uv sync (backend/) + npm install (frontend/) + pre-commit install
mise run dev        # uvicorn (hot-reload, :8000) + Vite dev server (:5173)
mise run check      # OpenAPI drift + lint + typecheck + test (what CI runs)
mise run openapi    # Regenerate shared/openapi.json and frontend API types
mise run db:migrate # alembic upgrade head
```

Open http://localhost:5173 — the page shows the backend's `/api/health` status.

Configure via environment variables (see [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md)).

## Docker

Requires Docker with the Compose plugin. No Python or Node install needed.

```bash
docker compose up --build   # or: mise run docker:up
```

Open http://localhost:8000. One container serves both the API and the compiled frontend, and runs `alembic upgrade head` before starting.

- **Data** lives in the `data` named volume, mounted at `/data` (SQLite at `/data/wealth.db`). It survives `docker compose down` and image rebuilds; `docker compose down -v` deletes it.
- **Config** via environment variables, e.g. `PORT=9000 LOG_LEVEL=debug docker compose up`:

  | Variable | Default | Purpose |
  |----------|---------|---------|
  | `PORT` | `8000` | Port uvicorn listens on, published on the host |
  | `LOG_LEVEL` | `info` | `critical`, `error`, `warning`, `info` or `debug` |
  | `DATA_DIR` | `/data` | SQLite location inside the container |

> **Security:** the app has no authentication ([ADR 0007](docs/adr/0007-no-authentication.md)). `docker-compose.yml` publishes the port on `127.0.0.1` only. Binding it to `0.0.0.0`, or putting it behind a reverse proxy without authentication, exposes all portfolio data to anyone who can reach it ([ADR 0019](docs/adr/0019-privacy-and-security-posture.md)).

## What's Runnable Today

- The app skeleton via `mise run dev` (see Quick Start) or `docker compose up --build` (see Docker)
- `python scripts/generate_mock_cams_pdf.py [output.pdf]` — generates a synthetic CAMS CAS PDF for testing
- Open `prototypes/cams-import/index.html` and `prototypes/screens-nav/index.html` in a browser to explore the UI design concepts

## Documentation

- **[CONTEXT.md](CONTEXT.md)** — glossary and domain language
- **[docs/adr/](docs/adr/)** — 22 architecture decision records covering the full design
- **[docs/research/](docs/research/)** — research on third-party data sources and formats
- **[AGENTS.md](AGENTS.md)** — conventions for AI agents working on this repo

## License

[AGPL-3.0](LICENSE) — see the `LICENSE` file for the full text.
