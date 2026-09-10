from collections.abc import Iterable

from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source


def _inline_fractions(source: Source, tokens: tuple[Token, ...]) -> Iterable[Finding]:
    """Report inline frac commands using this module's rule metadata."""
    for token in tokens:
        if token.kind == "command" and token.value == r"\frac" and token.math == "inline":
            yield source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="MATH-04",
    explanation=r"Avoid \frac in inline math; reserve fractions for displayed equations.",
    correction=r"Use a slash such as $a/b$, a negative exponent such as $s^{-1}$, \sfrac from the xfrac package or move the fraction to display math.",
    passing_examples=(r"$a/b$", r"$s^{-1}$", r"\[\frac{a}{b}\]"),
    failing_examples=(r"$\frac{a}{b}$", r"\(\frac{a}{b}\)"),
    limits=(
        r"Detects literal \frac commands in $...$, \(...\), and the math environment, "
        "including nested arguments and multiline input. Reports the command's backslash. "
        r"Display delimiters are $$...$$ and \[...\]; display environments are displaymath, "
        "equation, align, alignat, gather, multline, flalign, eqnarray, and their starred forms "
        "except displaymath*. Comments, \\verb, \\verb*, verbatim, verbatim*, lstlisting, and minted "
        "are excluded. Environment names must be literal, with no comments inside the begin/end command. "
        r"Does not expand macros, interpret text-mode command arguments, check \dfrac, \tfrac, "
        "or validate LaTeX syntax. Unclosed math continues to end of file; an unclosed literal "
        "environment consumes the rest of the file. Includes are not followed yet."
    ),
    evaluate=_inline_fractions,
)
