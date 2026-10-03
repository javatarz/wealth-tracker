# Code style

Code in this repo follows Object Calisthenics, SOLID and clean-code practice
(ADR 0028). Most of the rules below fail lint (ruff, ESLint, a small AST check,
pre-commit, and `mise run check` in CI), so you find out on commit, not in
review. The rest are review rules. Apply them while writing code, not after lint
complains.

## Rules and how they're enforced

| Rule | Python | TypeScript (ESLint) |
|---|---|---|
| No `else` / `elif` | `lint:calisthenics` (also `RET505`–`RET508`) | `no-restricted-syntax` on `if … else`, `no-else-return` |
| No if ladders (consecutive `if`s) | `lint:calisthenics` | `no-restricted-syntax` on `IfStatement + IfStatement` |
| One level of indentation per function | `PLR1702` max-nested-blocks = 1 | `max-depth` 1 |
| Small functions | `PLR0915` ≤ 12 statements, `C901` complexity ≤ 4, `PLR0912` ≤ 4 branches, `PLR0911` ≤ 3 returns | `max-statements` 10, `complexity` 4, `max-lines-per-function` 40 |
| Few arguments | `PLR0913`/`PLR0917` ≤ 3 | `max-params` 3 |
| Few locals | `PLR0914` ≤ 7 | — |
| Small files and classes | `PLR0904` ≤ 7 public methods | `max-lines` 150 per file |
| No flag (boolean) arguments | `FBT` | review |
| No magic values | `PLR2004` (not in tests) | review |
| No commented-out code, no unused arguments | `ERA`, `ARG` | `no-unused-vars` |
| No nested ternaries | — | `no-nested-ternary` |

When behaviour varies by kind, put the variants in a lookup table keyed by the
kind, and reach it through a guard clause rather than a branch per kind.
Examples: `transitions` in `frontend/src/statements/importState.ts` and
`outcomes` in `ImportOutcome.tsx`.

## Review rules

No linter can check these reliably:

- **Single responsibility.** Each module, class, component and function has one
  reason to change. Split parsing from presentation, I/O from mapping, and state
  transitions from rendering.
- **Depend on abstractions.** Infrastructure (casparser, the database, HTTP)
  sits behind a function type or `Protocol` and is passed in. In FastAPI that
  means `Depends(...)`, so tests can swap it with `app.dependency_overrides`.
- **Open/closed.** Add a new kind by adding an entry to a lookup table, not by
  editing a conditional.
- **Tell, don't ask.** Put behaviour on the object that owns the data
  (`StatementUpload.password_error()`, `ParsedStatement.previewed_by()`).
- **Wrap primitives that carry domain meaning.** Use value objects for things
  that have rules (`StatementUpload`). Plain `str`/`bytes` are fine at the
  framework boundary.
- **One dot per line** (Law of Demeter). Don't reach through objects you were
  handed.
- **No abbreviations.** Write `transaction`, not `txn`. Names say what a thing
  is, not how it's built.
- **Name errors after what went wrong.** Use factory classmethods
  (`StatementParseError.not_a_pdf()`) instead of repeating code/message pairs.

## Exemptions

- **Schema models.** Pydantic API models, generated OpenAPI types and TypeScript
  response types mirror an external shape. They are exempt from "first-class
  collections", "wrap all primitives" and "two instance variables". They still
  carry no behaviour beyond simple mapping.
- **Tests.** Test files may have long `describe`/`it` bodies and literal status
  codes. The nesting, complexity, no-`else` and no-ladder rules still apply.
- **Suppressing a rule** (`# noqa: <rule>` or
  `// eslint-disable-next-line <rule>`) needs a reason on the same line, and you
  need to be able to defend it. Prefer refactoring.
