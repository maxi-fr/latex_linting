from collections.abc import Callable, Iterable
from dataclasses import dataclass

from latex_linting.scanner import Token
from latex_linting.source import Finding, Source


@dataclass(frozen=True)
class Rule:
    """Keep a rule's evaluator and author-facing documentation in one entry."""

    rule_id: str
    explanation: str
    correction: str
    passing_examples: tuple[str, ...]
    failing_examples: tuple[str, ...]
    limits: str
    evaluate: Callable[[Source, tuple[Token, ...]], Iterable[Finding]]
