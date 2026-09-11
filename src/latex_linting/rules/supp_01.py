from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(_document: "Document") -> Iterable[Finding]:
    """Yield no findings directly because SUPP-01 findings are synthesized during suppression processing."""
    return ()


RULE = Rule(
    rule_id="SUPP-01",
    explanation="Source directive suppresses a rule that was not violated in its scope.",
    correction="Remove the unused rule ID from the directive, or remove the entire directive.",
    passing_examples=(
        r"$\frac{a}{b}$ % latex-lint:ignore=MATH-04",
        "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04",
    ),
    failing_examples=(
        r"$a/b$ % latex-lint:ignore=MATH-04",
        "% latex-lint:disable=MATH-04\n$a/b$\n% latex-lint:enable=MATH-04",
    ),
    limits=(
        "Detects ignore directives on lines with no matching finding, and disable directives where the "
        "suppressed rule does not trigger before a matching enable or the end of the file. In multi-rule "
        "directives, only the unused rule IDs are flagged."
    ),
    evaluate=_evaluate,
)
