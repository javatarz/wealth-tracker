# Wealth Tracker

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

> **Note:** The stack is still being scaffolded. These commands are planned per the ADRs — expect them to work once the initial project structure lands.

```bash
mise install        # Install pinned Python, Node, uv, npm
mise run install    # uv sync (backend/) + npm install (frontend/)
mise run dev        # uvicorn (hot-reload) + Vite dev server
mise run check      # lint + typecheck + test
mise run db:migrate # alembic upgrade head
mise run docker:up  # docker compose up
```

Configure via environment variables (see [ADR 0018](docs/adr/0018-repo-layout-api-contract-and-packaging.md)).

## What's Runnable Today

- `python scripts/generate_mock_cams_pdf.py [output.pdf]` — generates a synthetic CAMS CAS PDF for testing
- Open `prototypes/cams-import/index.html` and `prototypes/screens-nav/index.html` in a browser to explore the UI design concepts

## Documentation

- **[CONTEXT.md](CONTEXT.md)** — glossary and domain language
- **[docs/adr/](docs/adr/)** — 22 architecture decision records covering the full design
- **[docs/research/](docs/research/)** — research on third-party data sources and formats
- **[AGENTS.md](AGENTS.md)** — conventions for AI agents working on this repo

## License

Not yet decided.