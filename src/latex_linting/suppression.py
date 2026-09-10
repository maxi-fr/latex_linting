import re
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from latex_linting.rules.catalogue import validate_rule_id
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_DIRECTIVE_PREFIX = re.compile(r"^%\s*latex-lint\s*:")
_DIRECTIVE_RE = re.compile(r"^%\s*latex-lint\s*:\s*([a-zA-Z_-]+)\s*=\s*(.+?)\s*$")
_VALID_ACTIONS = frozenset({"ignore", "disable", "enable"})


@dataclass(frozen=True)
class Directive:
    """Record a parsed source directive and its location."""

    action: str
    rule_ids: frozenset[str]
    offset: int
    line: int


def parse_directives(source: Source, tokens: Sequence[Token]) -> tuple[Directive, ...]:
    """Parse and validate source directives from scanned comment tokens."""
    directives = []
    for token in tokens:
        if token.kind != "comment":
            continue
        if not _DIRECTIVE_PREFIX.match(token.value):
            continue
        line = source.line_number(token.start)
        match = _DIRECTIVE_RE.match(token.value)
        if match is None:
            msg = f"malformed latex-lint directive in {source.filename} line {line}: {token.value}"
            raise ValueError(msg)
        action = match.group(1)
        if action not in _VALID_ACTIONS:
            msg = f"unknown directive action '{action}' in {source.filename} line {line}"
            raise ValueError(msg)
        raw_ids = match.group(2)
        id_parts = [part.strip() for part in raw_ids.split(",")]
        if any(not part for part in id_parts):
            msg = f"empty rule ID in directive in {source.filename} line {line}: {token.value}"
            raise ValueError(msg)
        for rule_id in id_parts:
            validate_rule_id(rule_id)
        directives.append(Directive(action, frozenset(id_parts), token.start, line))
    return tuple(directives)


def filter_findings(
    source: Source,
    findings: Iterable[Finding],
    directives: Sequence[Directive],
    ignored_rules: Collection[str] | None = None,
) -> list[Finding]:
    """Filter out findings suppressed by invocation-wide exclusions or source directives."""
    ignored_set = frozenset(ignored_rules) if ignored_rules else frozenset()
    same_line_ignores: dict[int, set[str]] = {}
    for directive in directives:
        if directive.action == "ignore":
            same_line_ignores.setdefault(directive.line, set()).update(directive.rule_ids)
    state_directives = [directive for directive in directives if directive.action in {"disable", "enable"}]
    kept = []
    for finding in findings:
        if finding.rule_id in ignored_set:
            continue
        if finding.rule_id in same_line_ignores.get(finding.line, ()):
            continue
        finding_offset = source.offset_of(finding.line, finding.column)
        is_disabled = False
        for directive in state_directives:
            if directive.offset > finding_offset:
                break
            if finding.rule_id in directive.rule_ids:
                is_disabled = directive.action == "disable"
        if not is_disabled:
            kept.append(finding)
    return kept
