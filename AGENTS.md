## Code style

Code follows Object Calisthenics, SOLID and clean-code rules. Read `docs/agents/code-style.md` before writing code. Lint enforces most of it (ADR 0028), so run `pre-commit run --all-files` or `mise run lint` early and often.

## Agent skills

### Issue tracker

Issues tracked in GitHub via `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role triage labels. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.
