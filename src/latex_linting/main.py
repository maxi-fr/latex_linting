from collections.abc import Collection
from pathlib import Path

from latex_linting.rules.catalogue import RULES, validate_rule_id
from latex_linting.scanner import scan
from latex_linting.source import Finding, Source
from latex_linting.suppression import filter_findings, parse_directives


def check(root: str | Path, ignored_rules: Collection[str] | None = None) -> list[Finding]:
    """Check one UTF-8 source file for rule violations, applying suppressions."""
    if ignored_rules is not None:
        for rule_id in ignored_rules:
            validate_rule_id(rule_id)
    with Path(root).open(encoding="utf-8", newline="") as handle:
        source = Source(str(root), handle.read())
    tokens = scan(source.text)
    directives = parse_directives(source, tokens)
    findings = [finding for rule in RULES for finding in rule.evaluate(source, tokens)]
    filtered = filter_findings(source, findings, directives, ignored_rules)
    return sorted(filtered, key=lambda finding: (finding.line, finding.column, finding.rule_id))
