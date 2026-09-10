import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_ABBREVIATION_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9\\])\b([eE]\.(?:[ \t~]+)?[gG]\.|[iI]\.(?:[ \t~]+)?[eE]\.)(?![a-zA-Z0-9])"
)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document prose for English abbreviations missing thin spaces."""
    for source, token in iter_prose_tokens(document):
        for match in _ABBREVIATION_PATTERN.finditer(token.value):
            offset = token.start + match.start()
            yield source.finding(offset, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="TYPO-03",
    explanation=r"Use prescribed thin space '\,' within abbreviations 'e.\,g.' and 'i.\,e.'.",
    correction=r"Format the abbreviation with a thin space: 'e.\,g.' or 'i.\,e.'.",
    passing_examples=(
        r"Consider, e.\,g., standard models.",
        r"This holds, i.\,e., without loss of generality.",
    ),
    failing_examples=(
        r"Consider, e.g., standard models.",
        r"Consider, e. g., standard models.",
        r"This holds, i.e., without loss of generality.",
    ),
    limits=(
        r"Checks English abbreviations 'e.g.' and 'i.e.' (and capitalized 'E.g.', 'I.e.') in "
        r"text mode. Enforces thin space 'e.\,g.' and 'i.\,e.'. Excludes math mode, comments, "
        "literal environments, and syntax command arguments. German abbreviation profiles are not introduced."
    ),
    evaluate=_evaluate,
)
