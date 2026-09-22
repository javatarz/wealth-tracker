# Monorepo with backend/ and frontend/, API contract enforced by OpenAPI codegen, single Docker image

## Layout

```
wealth-tracker/
  backend/         # FastAPI app
    app/
      api/         # endpoint modules
      core/        # config, database, market-data clients
      domain/      # valuation, XIRR, benchmarking, projections
    tests/
    alembic/       # schema migrations
    pyproject.toml
  frontend/        # React SPA
    src/
    public/
    package.json
  shared/          # OpenAPI spec as source of truth (generated, committed)
  mise.toml
  docker-compose.yml
```

## API contract enforcement

FastAPI generates OpenAPI 3.0 from Pydantic models. CI regenerates TypeScript types
via `openapi-typescript` and fails if `git diff` detects drift. Developers never
hand-write API client types.

## Packaging

Single Docker image — uvicorn serves the API with compiled frontend assets baked in
as static files. SQLite on a mounted volume (`-v data:/data`). No nginx or sidecar.
`docker-compose.yml` is the primary deploy path; `mise run dev` is the documented
non-Docker alternative.

## mise tasks

| Task | Runs |
|------|------|
| `install` | `uv sync` in `backend/`, `npm install` in `frontend/` |
| `dev` | uvicorn (hot-reload) + Vite dev server concurrently |
| `test` | `uv run pytest` in `backend/`, `npm test` in `frontend/` |
| `lint` | `uv run ruff` in `backend/`, `npx eslint` in `frontend/` |
| `typecheck` | `uv run mypy --strict` in `backend/`, `npx tsc --noEmit` in `frontend/` |
| `check` | lint + typecheck + test |
| `db:migrate` | `uv run alembic upgrade head` |
| `docker:build` | `docker compose build` |
| `docker:up` | `docker compose up` |

## Configuration

Environment variables read at startup via Pydantic `Settings`. `.env` file supported
in dev. Variables:

- `DATA_DIR` (default `./data`) — SQLite file location
- `PORT` (default 8000)
- `LOG_LEVEL` (default `info`)
- `CORS_ORIGINS` (default `http://localhost:5173` — Vite dev server)

## Consequences

- A new contributor runs `mise install` and `mise run dev`; everything works without
  Docker if Python and Node are installed via mise.
- The OpenAPI spec is committed so `git diff` catches drift, but its primary audience
  is the codegen tool, not humans.
- `uv run` prefixes every Python task because uv's venv is not implicitly on `$PATH`
  inside mise tasks. This is explicit but slightly noisy.
- The backend type checker is `mypy --strict`; ADR-0026 supersedes this ADR's
  original choice of `pyright` and sets the strictness posture for both languages.