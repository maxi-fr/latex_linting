from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(_document: "Document") -> Iterable[Finding]:
    """Yield no findings directly because SUPP-02 findings are synthesized during suppression processing."""
    return ()


RULE = Rule(
    rule_id="SUPP-02",
    explanation="Directive attempts to enable a rule that is not disabled, or disable a rule that is already disabled.",
    correction="Remove the redundant enable or disable directive.",
    passing_examples=(
        "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04",
    ),
    failing_examples=(
        "% latex-lint:enable=MATH-04\n$\\frac{a}{b}$",
        "% latex-lint:disable=MATH-04\n% latex-lint:disable=MATH-04",
    ),
    limits=(
        "Detects enable directives for rules that are not currently disabled in the source file, "
        "and disable directives for rules that are already disabled. "
        "Only source file directives within the same file are tracked."
    ),
    evaluate=_evaluate,
)
