import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.math_context import iter_math_tokens
from latex_linting.rules.model import Rule
from latex_linting.source import Finding

_STANDARD_FUNCTIONS = (
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "coth",
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "exp",
    "ln",
    "log",
    "lg",
    "min",
    "max",
    "sup",
    "inf",
    "lim",
    "det",
    "dim",
    "ker",
    "gcd",
    "hom",
    "arg",
    "deg",
    "Pr",
)

_FUNCTION_PATTERN = re.compile(r"(?<![a-zA-Z])(" + "|".join(_STANDARD_FUNCTIONS) + r")(?![a-zA-Z])")


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report standard mathematical functions set as italic text rather than upright commands."""
    for source, token, ctx in iter_math_tokens(document):
        if not ctx.in_math or ctx.in_non_math or ctx.in_upright:
            continue
        if token.kind != "text":
            continue

        for match in _FUNCTION_PATTERN.finditer(token.value):
            func_name = match.group(1)
            func_offset = token.start + match.start()
            correction = f"Use \\{func_name} instead of {func_name}."
            yield source.finding(func_offset, RULE.rule_id, RULE.explanation, correction)


RULE = Rule(
    rule_id="MATH-12",
    explanation=(
        "Standard mathematical functions and operators must be set upright using LaTeX "
        r"commands (e.g. \sin, \cos, \exp, \min) rather than italic variable products."
    ),
    correction=r"Use standard LaTeX upright function commands (e.g. \sin, \cos, \exp).",
    passing_examples=(
        r"$\sin(x)$",
        r"$\cos(\theta)$",
        r"$\exp(-t)$",
        r"\[ \lim_{x \to 0} f(x) \,.\]",
        r"$\min(a, b)$",
        r"$e^{i\pi} + 1 = 0$",
    ),
    failing_examples=(
        "$sin(x)$",
        r"$cos(\theta)$",
        "$exp(-t)$",
        r"\[ lim_{x \to 0} f(x) \]",
        "$min(a, b)$",
    ),
    limits=(
        "Detects recognized standard functions and operators (sin, cos, tan, exp, ln, log, "
        "min, max, sup, inf, lim, det, arg, deg, and hyperbolic/inverse variants) written as "
        "italic text in math mode rather than standard LaTeX upright commands. Upright macros "
        r"and arguments of \mathrm, \operatorname, or \text are accepted. Single-letter "
        "constants (e.g. e, i) and differential operators are not inferred. Comments, literal "
        "code, and nested non-math commands are excluded."
    ),
    evaluate=_evaluate,
)
