import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_THIS_VERBS = frozenset(
    {
        "can",
        "could",
        "demonstrates",
        "does",
        "had",
        "has",
        "illustrates",
        "indicates",
        "is",
        "leads",
        "may",
        "means",
        "might",
        "must",
        "proves",
        "provides",
        "represents",
        "should",
        "shows",
        "suggests",
        "was",
        "will",
        "would",
    }
)

_THESE_VERBS = frozenset(
    {
        "are",
        "can",
        "could",
        "demonstrate",
        "do",
        "had",
        "have",
        "illustrate",
        "indicate",
        "lead",
        "may",
        "mean",
        "might",
        "must",
        "prove",
        "provide",
        "represent",
        "should",
        "show",
        "suggest",
        "were",
        "will",
        "would",
    }
)

_PATTERN = re.compile(
    r"(?:(?<=[.?!:;'\u201c\u201d\u2018\u2019()\[\]\u2014\u2013\"-])|(?<=\A)|(?<=[\r\n]))\s*\b(This|These)\s+([a-zA-Z]+)\b"
)


def _standalone_demonstratives(document: "Document") -> Iterable[Finding]:
    """Report standalone This or These without an explicit referent noun."""
    for source, token in iter_prose_tokens(document):
        for match in _PATTERN.finditer(token.value):
            demonstrative = match.group(1)
            verb = match.group(2).lower()
            is_violation = (demonstrative == "This" and verb in _THIS_VERBS) or (
                demonstrative == "These" and verb in _THESE_VERBS
            )
            if is_violation:
                offset = token.start + match.start(1)
                yield source.finding(offset, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="PROSE-02",
    explanation="Avoid standalone 'This' or 'These' without a referent noun; name what is being referred to.",
    correction="Add an explicit referent noun after the demonstrative (e.g. 'This method...', 'These results...').",
    passing_examples=(
        "This approach demonstrates substantial improvements in accuracy.",
        "These results indicate that the hypothesis is valid.",
        "In this section, we introduce the proposed architecture.",
    ),
    failing_examples=(
        "This is an important result for our evaluation.",
        "These show that the controller stabilizes the system.",
        "This demonstrates the effectiveness of the algorithm.",
    ),
    limits=(
        "Heuristic check detecting standalone 'This' or 'These' at sentence start or after "
        "punctuation immediately followed by common verbs (is, are, was, were, has, have, "
        "shows, show, demonstrates, demonstrate, indicates, indicate, leads, lead, means, mean, "
        "suggests, suggest, illustrates, illustrate, proves, prove, can, could, will, would). "
        "Does not detect standalone demonstratives separated from the verb by adverbs "
        "(e.g. 'This clearly shows'), standalone demonstratives functioning as grammatical "
        "objects, or lowercase demonstratives mid-sentence. Comments, math mode, and literal "
        "environments are excluded."
    ),
    evaluate=_standalone_demonstratives,
)
