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

All per [ADR 0011](docs/adr/0011-stack.md) / [ADR 0012](docs/adr/0012-mise-and-docker.md) / [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md).

## Quick Start

```bash
# Prerequisites: install mise (https://mise.jdx.dev)
mise install         # Install pinned Python 3.12, Node 22, uv
mise run install     # uv sync (backend/) + npm install (frontend/) + pre-commit hooks
mise run dev         # uvicorn (hot-reload at :8000) + Vite dev server (:5173)
mise run check       # lint + typecheck + test + OpenAPI drift check
mise run db:migrate  # alembic upgrade head
```

> **Docker:** `docker compose up` support will be added later (ADR 0012).

Configure via environment variables (see [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md)).

## What's Runnable Today

- `mise run dev` — starts backend (port 8000) and frontend (port 5173) concurrently
- `mise run check` — runs lint, typecheck, test, and OpenAPI drift check
- `mise run db:migrate` — applies Alembic migrations
- `python scripts/generate_mock_cams_pdf.py [output.pdf]` — generates a synthetic CAMS CAS PDF for testing
- Open `prototypes/cams-import/index.html` and `prototypes/screens-nav/index.html` in a browser to explore the UI design concepts

## Documentation

- **[CONTEXT.md](CONTEXT.md)** — glossary and domain language
- **[docs/adr/](docs/adr/)** — 22 architecture decision records covering the full design
- **[docs/research/](docs/research/)** — research on third-party data sources and formats
- **[AGENTS.md](AGENTS.md)** — conventions for AI agents working on this repo

## License

[AGPL-3.0](LICENSE) — see the `LICENSE` file for the full text.
