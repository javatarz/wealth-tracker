"""Object Calisthenics checks ruff can't express (ADR 0028): no else, no if ladders."""

import ast
import sys
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path

_ELSE = "don't use else/elif; return early or use a lookup"
_LADDER = "if ladder; replace consecutive ifs with a lookup or polymorphism"
_ELSE_OWNERS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try)
_BLOCK_OWNERS = (
    ast.Module,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.ExceptHandler,
)

Problem = tuple[int, str]


def main(roots: list[str]) -> int:
    findings = [finding for path in _python_files(roots) for finding in _findings(path)]
    sys.stdout.writelines(f"{finding}\n" for finding in findings)
    return int(bool(findings))


def _python_files(roots: list[str]) -> Iterator[Path]:
    for root in roots:
        yield from sorted(Path(root).rglob("*.py"))


def _findings(path: Path) -> Iterator[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        yield from (f"{path}:{line}: {message}" for line, message in _problems(node))


def _problems(node: ast.AST) -> Iterator[Problem]:
    yield from _else_problems(node)
    yield from _ladder_problems(node)


def _else_problems(node: ast.AST) -> Iterator[Problem]:
    if isinstance(node, _ELSE_OWNERS) and node.orelse:
        yield node.lineno, _ELSE


def _ladder_problems(node: ast.AST) -> Iterator[Problem]:
    if isinstance(node, _BLOCK_OWNERS):
        yield from (
            (second.lineno, _LADDER)
            for first, second in pairwise(node.body)
            if isinstance(first, ast.If) and isinstance(second, ast.If)
        )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
