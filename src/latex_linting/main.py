from collections.abc import Collection
from pathlib import Path

from latex_linting.document import load_document, ordered_findings
from latex_linting.rules.catalogue import validate_rule_id
from latex_linting.source import Finding

__all__ = ["Finding", "check"]


def check(root: str | Path, ignored_rules: Collection[str] | None = None) -> list[Finding]:
    """Check a LaTeX root document and its included files, applying suppressions."""
    if ignored_rules is not None:
        for rule_id in ignored_rules:
            validate_rule_id(rule_id)
    document = load_document(root)
    return ordered_findings(document, ignored_rules)
