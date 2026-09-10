import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_PATTERN = re.compile(r",\s+that\b")


def _comma_before_that(document: "Document") -> Iterable[Finding]:
    """Report suspected comma-before-that violations in English prose."""
    for source, token in iter_prose_tokens(document):
        for match in _PATTERN.finditer(token.value):
            offset = token.start + match.start()
            yield source.finding(offset, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="PROSE-03",
    explanation=(
        "Suspected comma-before-that violation; restrictive clauses with 'that' should not be "
        "preceded by a comma unless part of a parenthetical phrase."
    ),
    correction="Remove the comma before 'that', or verify whether a parenthetical phrase or idiom justifies it.",
    passing_examples=(
        "We found that the proposed algorithm converges rapidly.",
        "The hypothesis that performance improves was confirmed.",
    ),
    failing_examples=(
        "We found, that the proposed algorithm converges rapidly.",
        "It is evident, that this parameter choice is suboptimal.",
    ),
    limits=(
        "Heuristic check detecting suspected comma-before-that constructions in English prose. "
        "Cannot perform full grammatical parsing to distinguish restrictive clauses from "
        "non-restrictive parentheticals or idioms (such as 'given that' or 'provided that'). "
        "Comments, literal code, math mode, and command syntax arguments are excluded."
    ),
    evaluate=_comma_before_that,
)
