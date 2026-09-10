from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_DISPLAY_ENVIRONMENTS = frozenset(
    {
        "displaymath",
        "equation",
        "equation*",
        "align",
        "align*",
        "alignat",
        "alignat*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "flalign",
        "flalign*",
        "eqnarray",
        "eqnarray*",
    }
)


def _is_display_math_open(token: Token) -> bool:
    """Return True if the token opens a recognized display math equation."""
    if token.kind == "command" and token.value == r"\[":
        return True
    if token.kind == "delimiter" and token.value == "$$":
        return True
    if token.kind == "environment" and token.value.startswith(r"\begin"):
        name = token.value[token.value.index("{") + 1 : -1]
        return name in _DISPLAY_ENVIRONMENTS
    return False


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report colons immediately preceding a displayed equation across the document."""
    prev_source: Source | None = None
    prev_token: Token | None = None

    for source, token in document.traverse():
        if token.kind == "comment" or (token.kind == "text" and token.value.isspace()):
            continue

        if (
            _is_display_math_open(token)
            and prev_token is not None
            and prev_source is not None
            and prev_token.math == "text"
            and prev_token.kind == "text"
        ):
            stripped = prev_token.value.rstrip()
            if stripped.endswith(":"):
                colon_idx = prev_token.value.rfind(":")
                colon_offset = prev_token.start + colon_idx
                yield prev_source.finding(colon_offset, RULE.rule_id, RULE.explanation, RULE.correction)

        prev_source = source
        prev_token = token


RULE = Rule(
    rule_id="PROSE-07",
    explanation="Do not place a colon immediately before a displayed equation; fold the equation into the sentence syntax.",
    correction="Remove the colon before the displayed equation and integrate the formula into the sentence.",
    passing_examples=(
        "The energy relation is\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}",
        "We compute the value as\n\\[\n  a = b + c \\,.\n\\]",
    ),
    failing_examples=(
        "The energy relation is:\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}",
        "We compute the value as: % note\n\\[\n  a = b + c \\,.\n\\]",
    ),
    limits=(
        "Reports a colon in text mode immediately preceding a recognized displayed equation (equation, "
        "align, gather, multline, alignat, flalign, eqnarray, their starred forms, displaymath, \\[...\\], "
        "or $$...$$). Whitespace and comments between the colon and the equation are ignored. Reports the "
        "colon's location. Does not verify broader grammatical correctness or sentence structure."
    ),
    evaluate=_evaluate,
)
