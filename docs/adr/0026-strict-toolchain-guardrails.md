# Strict toolchain guardrails for agent-written code

A large share of this codebase will be written by coding agents, which produce
plausible but wrong code: untyped functions, `Any` leaking through call chains,
strings coerced into numbers, and raw SQL assembled by hand. The organising
principle is that the toolchain should **reject** bad code at build time rather
than rely on review to catch it. Constraints that fail the build are preferred
over conventions that only warn.

## Decision

**Python.** `mypy --strict` (with the Pydantic plugin) is the type checker;
`pyright` is not used. `ruff` lints and formats. Strict mode is chosen for the
checks that catch agent mistakes — `disallow_untyped_defs`,
`disallow_any_expr`, `disallow_any_explicit`, `warn_unreachable`.

**TypeScript.** `tsconfig` enables `strict` plus `noUncheckedIndexedAccess`,
`exactOptionalPropertyTypes`, and `noPropertyAccessFromIndexSignature`. These
catch assuming a missing key exists, forgetting `undefined`, and confusing
index signatures with declared properties.

**Pydantic.** Every model sets `model_config = {"strict": True}`. No implicit
coercion, so a string arriving where a number is expected fails at the boundary
instead of propagating.

**Pre-commit.** `pre-commit` runs lint, format, and type checks on every
commit — `ruff`, `ruff-format`, `mypy --strict`, `eslint`, `prettier`,
`tsc --noEmit`, file-hygiene hooks, and `editorconfig-checker` (enforcing
`.editorconfig`: final newline, LF, 2-space indent except Python's 4) — so formatting and type errors are
blocked before they reach a commit. A `pre-push` hook runs the tests and the
OpenAPI drift check, so the CI safety net runs locally before anything leaves the
machine. `mise run check` (drift, every hook, tests) remains the full gate in
CI. One config file covers both ecosystems; `husky` and `lint-staged` are not used.

**Data access.** Queries go through the SQLAlchemy 2.0 ORM and Alembic
migrations. Application code does not assemble SQL inline. Where the ORM cannot
express a query, the escape hatch lives in a named module under
`backend/app/core/queries/` with its own test.

## Considered Options

- **`pyright` or `basedpyright` instead of `mypy --strict`**: faster, but its
  strict modes are less of a recognised standard and its `Any` handling is
  looser. Speed is not the constraint at this scale.
- **`husky` + `lint-staged` for hooks**: would need a second config alongside
  `pre-commit` for the Python side. One framework covers both.
- **Advisory linting (warnings, not failures)**: agents treat warnings as
  noise. A failing build is the only signal that reliably changes output.

## Consequences

- Backend type checking moves from `pyright` to `mypy --strict`, superseding
  that choice in ADR-0018; its `typecheck` task runs `uv run mypy --strict`.
- `mypy --strict` is slower than `pyright`. Acceptable for a single-instance
  personal tool.
- Strict Pydantic models reject data that arrives as strings (form posts,
  URL params), so coercion becomes an explicit, tested step at the API
  boundary rather than an implicit one.
- Type checks in pre-commit make commits slower (seconds, growing with the
  codebase). Accepted: a type error caught at commit time is cheaper than one
  caught in CI.
- Tests on pre-push keep the suite under pressure to stay fast; a slow suite
  shows up as a slow push.
- Raw-SQL escape hatches are a deliberate, discoverable directory, not a
  scattered pattern — a reviewer can grep one path.
