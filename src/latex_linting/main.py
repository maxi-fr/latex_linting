from pathlib import Path

from latex_linting.rules.catalogue import RULES
from latex_linting.scanner import scan
from latex_linting.source import Finding, Source


def check(root: str | Path) -> list[Finding]:
    """Check one UTF-8 source file; propagate file and decoding errors to callers."""
    with Path(root).open(encoding="utf-8", newline="") as handle:
        source = Source(str(root), handle.read())
    tokens = scan(source.text)
    findings = [finding for rule in RULES for finding in rule.evaluate(source, tokens)]
    return sorted(findings, key=lambda finding: (finding.line, finding.column, finding.rule_id))
