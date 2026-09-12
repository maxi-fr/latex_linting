from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.source import Finding


@dataclass(frozen=True)
class Rule:
    """Keep a rule's evaluator and author-facing documentation in one entry."""

    rule_id: str
    explanation: str
    correction: str
    passing_examples: tuple[str, ...]
    failing_examples: tuple[str, ...]
    limits: str
    evaluate: Callable[["Document"], Iterable[Finding]]
    enabled_by_default: bool = True
