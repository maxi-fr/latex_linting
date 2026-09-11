import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.math_context import iter_math_tokens
from latex_linting.rules.model import Rule
from latex_linting.source import Finding

_DECIMAL_COMMA = re.compile(r"(?<!\d)(\d+),(\d+)(?!\d)")


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report suspected decimal commas in English math mode across the document."""
    for source, token, ctx in iter_math_tokens(document):
        if not ctx.in_math or ctx.in_non_math or ctx.in_index:
            continue
        if token.kind != "text":
            continue

        for match in _DECIMAL_COMMA.finditer(token.value):
            comma_offset = token.start + match.start() + len(match.group(1))
            yield source.finding(comma_offset, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="MATH-14",
    explanation=(
        "Suspected decimal comma in English math mode. In English, use a period as the decimal "
        "separator (e.g. 3.14). If this is an intentional decimal comma in a German passage, "
        "wrap the comma in braces ({,}). If this is a comma-separated list or coordinate pair "
        "without spaces (e.g. (1,2)), add a space after the comma."
    ),
    correction=(
        "Use a period for decimal quantities in English math (e.g. 3.14), wrap the decimal "
        "comma in braces ({,}), or add a space after the comma for lists and coordinates."
    ),
    passing_examples=(
        "$3.14$",
        "$3{,}14$",
        "$(1, 2)$",
        "$x_{1,1}$",
        r"\[ x = 0.05 \,.\]",
    ),
    failing_examples=(
        "$3,14$",
        r"\[ x = 0,05 \]",
        "$(1,2)$",
    ),
    limits=(
        r"Detects adjacent digits separated by a comma without whitespace (\d+,\d+) in inline "
        "and display math. Wrapped commas such as 3{,}14 are accepted. Coordinates and lists "
        "without whitespace (e.g. (1,2)) are flagged due to ambiguity with decimals; add spaces "
        "after commas to disambiguate. Subscripts and superscripts (e.g. x_{1,1}), comments, "
        "literal code, and nested non-math commands are excluded. Does not verify document language."
    ),
    evaluate=_evaluate,
)
