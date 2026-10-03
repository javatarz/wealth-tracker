# Object Calisthenics, SOLID and clean-code rules enforced by lint

Coding agents write most of this codebase. Left to themselves they produce long
functions that do several jobs, nested conditionals, if ladders over a kind,
and infrastructure calls wired directly into request handlers. Review catches
some of this, but only if the maintainer notices every time. ADR 0026 decided
that the toolchain should reject bad code at build time rather than rely on
review. This ADR applies that principle to design as well as types.

## Decision

Code follows Object Calisthenics, SOLID and clean-code practice, written up for
agents in `docs/agents/code-style.md`. AGENTS.md points to that guide. Every
rule a linter can check fails the build, in the same places as ADR 0026's
checks: pre-commit on every commit, and `mise run check` in CI.

**Python.** Ruff adds `C90`, `PL`, `RET`, `FBT`, `ERA`, `ARG` and `PIE`, plus the
preview rules `PLR1702` (nesting), `PLR0914` (locals) and `PLR0917`
(positional arguments). `explicit-preview-rules` is set so that no other
preview rule turns on by accident. The limits are:

- complexity 4
- 4 branches
- 3 returns
- 12 statements
- 3 arguments
- 7 locals
- 1 nested block
- 7 public methods

Ruff can't ban `else` or if ladders, so `backend/scripts/check_calisthenics.py`
does it with a short AST walk. It runs as the `lint:calisthenics` mise task, as
a pre-commit hook, and as part of `lint:backend`.

**TypeScript (ESLint).** The limits are:

- `complexity` 4
- `max-depth` 1
- `max-params` 3
- `max-statements` 10
- `max-lines-per-function` 40
- `max-lines` 150
- `max-nested-callbacks` 3

`no-else-return` and `no-nested-ternary` are also on. `no-restricted-syntax`
bans `if … else` and consecutive `if` statements. Test files are exempt from
the size limits only.

Some rules can't be linted reliably: single responsibility, dependency
inversion, tell-don't-ask, Law of Demeter, wrapping domain primitives, and no
abbreviations. These are written down as review rules in the same guide.

## Considered Options

- **Guidance only, no lint**: agents treat prose guidelines as optional
  (ADR 0026). A failing build is what changes their output.
- **Pylint or wemake-python-styleguide**: these cover more of Object
  Calisthenics out of the box, but they would be a second Python linter. Ruff's
  pylint port covers the size limits, and about 60 lines of AST code cover the
  rest.
- **Banning conditional expressions as well as `else` statements**: too strict
  for one-line value choices. Nested ternaries are banned instead.

## Consequences

- The limits are deliberately tight. Expect many small functions and
  components, with behaviour that varies by kind held in lookup tables. When
  this ADR landed, the existing code was refactored to comply.
- Ruff preview rules can change between releases. Ruff is pinned in pre-commit
  and `uv.lock`, so a change only shows up on a deliberate upgrade.
- A rule may be suppressed only with a reason on the same line. Reviewers
  should treat a suppression as a design discussion, not a formality.
