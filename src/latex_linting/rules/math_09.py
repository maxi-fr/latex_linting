import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.math_context import iter_math_tokens
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding

_OPERATOR_PATTERN = re.compile(r"(&&|\|\||!=|~=|==|<=|>=|\.\*|\.\^|\./|\*\*|(?<![\^_\.\*])\*(?!\*))")

_REPLACEMENTS: dict[str, str] = {
    "*": r"\cdot",
    "**": "^",
    "!=": r"\neq",
    "~=": r"\neq",
    "==": "=",
    "<=": r"\le",
    ">=": r"\ge",
    "&&": r"\land",
    "||": r"\lor",
    ".*": r"\cdot",
    ".^": "^",
    "./": r"/ or \frac",
}


_MIN_SCRIPT_LOOKBACK = 2


def _is_script_asterisk(match_start: int, prev_tokens: list[Token]) -> bool:
    """Return True if the asterisk is inside a superscript or subscript brace group."""
    if match_start > 0:
        return False
    if len(prev_tokens) >= _MIN_SCRIPT_LOOKBACK and prev_tokens[-1].value == "{":
        lookback = prev_tokens[-2].value.rstrip()
        if lookback.endswith(("^", "_")):
            return True
    return False


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report programming operators in math mode across the document."""
    prev_tokens: list[Token] = []

    for source, token, ctx in iter_math_tokens(document):
        if not ctx.in_math or ctx.in_non_math:
            prev_tokens.append(token)
            continue
        if token.kind != "text":
            prev_tokens.append(token)
            continue

        for match in _OPERATOR_PATTERN.finditer(token.value):
            op = match.group(1)
            if op == "*" and _is_script_asterisk(match.start(), prev_tokens):
                continue
            op_offset = token.start + match.start()
            rep = _REPLACEMENTS.get(op, r"\cdot")
            correction = f"Use {rep} instead of '{op}'."
            yield source.finding(op_offset, RULE.rule_id, RULE.explanation, correction)

        prev_tokens.append(token)


RULE = Rule(
    rule_id="MATH-09",
    explanation=(
        "Programming operators (such as *, !=, ==, &&, ||, <=, >=, .*, .^, ./) must not "
        "be used in mathematical formulas."
    ),
    correction=(
        r"Use standard LaTeX mathematical notation such as \cdot (multiplication), "
        r"\neq (!=), = (==), \land (&&), \lor (||), \le (<=), or \ge (>=)."
    ),
    passing_examples=(
        r"$a \cdot b$",
        r"$x \neq y$",
        "$x = y$",
        r"$a \land b$",
        r"$x \le y$",
        "$x^*$",
    ),
    failing_examples=(
        "$a * b$",
        "$x != y$",
        "$x == y$",
        "$a && b$",
        "$a || b$",
        "$A .* B$",
    ),
    limits=(
        "Detects documented programming operators (*, !=, ==, &&, ||, <=, >=, ~=, .*, .^, "
        "./, **) in inline and display math. Ordinary LaTeX command backslashes (e.g. \\cdot, "
        r"\alpha, \frac) and superscript/subscript asterisks (e.g. x^*, x^{*}) are accepted. "
        "Comments, literal code, and nested non-math commands are excluded."
    ),
    evaluate=_evaluate,
)
