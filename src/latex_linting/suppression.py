import re
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from latex_linting.rules.catalogue import validate_rule_id
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_DIRECTIVE_PREFIX = re.compile(r"^%\s*latex-lint\s*:")
_DIRECTIVE_RE = re.compile(r"^%\s*latex-lint\s*:\s*([a-zA-Z_-]+)\s*=\s*(.+?)\s*$")
_VALID_ACTIONS = frozenset({"ignore", "disable", "enable"})


_META_RULES = frozenset({"SUPP-01", "SUPP-02"})


@dataclass(frozen=True)
class Directive:
    """Record a parsed source directive and its location."""

    action: str
    rule_ids: frozenset[str]
    offset: int
    line: int


@dataclass(frozen=True)
class _DisableSpan:
    """Record a range where a rule is disabled in a source file."""

    directive: Directive
    rule_id: str
    start: int
    end: int


@dataclass(frozen=True)
class _SuppressionState:
    """Group tracking state across suppression filtering passes."""

    used_ignores: set[tuple[int, str]]
    used_disables: set[tuple[Directive, str]]
    redundant_disables: set[tuple[Directive, str]]
    ignored_set: frozenset[str]


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


def _process_disable_directive(
    directive: Directive,
    source: Source,
    currently_disabled: dict[str, Directive],
    redundant_disables: set[tuple[Directive, str]],
    *,
    supp_02_enabled: bool,
) -> list[Finding]:
    """Record newly disabled rules or report redundant disable directives."""
    findings = []
    for rule_id in sorted(directive.rule_ids):
        if rule_id in currently_disabled:
            redundant_disables.add((directive, rule_id))
            if supp_02_enabled:
                findings.append(
                    source.finding(
                        directive.offset,
                        "SUPP-02",
                        f"redundant disable: rule '{rule_id}' is already disabled",
                        f"Remove the redundant disable directive for '{rule_id}'.",
                    )
                )
        else:
            currently_disabled[rule_id] = directive
    return findings


def _process_enable_directive(
    directive: Directive,
    source: Source,
    currently_disabled: dict[str, Directive],
    *,
    supp_02_enabled: bool,
) -> tuple[list[_DisableSpan], list[Finding]]:
    """Close active disable spans or report redundant enable directives."""
    spans = []
    findings = []
    for rule_id in sorted(directive.rule_ids):
        if rule_id not in currently_disabled:
            if supp_02_enabled:
                findings.append(
                    source.finding(
                        directive.offset,
                        "SUPP-02",
                        f"redundant enable: rule '{rule_id}' is not disabled",
                        f"Remove the redundant enable directive for '{rule_id}'.",
                    )
                )
        else:
            prev_directive = currently_disabled.pop(rule_id)
            spans.append(_DisableSpan(prev_directive, rule_id, prev_directive.offset, directive.offset))
    return spans, findings


def _analyze_state_directives(
    source: Source,
    directives: Sequence[Directive],
    ignored_set: frozenset[str],
) -> tuple[list[_DisableSpan], list[Finding], set[tuple[Directive, str]]]:
    """Analyze disable and enable directives for redundant transitions and active spans."""
    spans: list[_DisableSpan] = []
    redundant_findings: list[Finding] = []
    redundant_disables: set[tuple[Directive, str]] = set()
    currently_disabled: dict[str, Directive] = {}
    supp_02_enabled = "SUPP-02" not in ignored_set

    for directive in directives:
        if directive.action == "disable":
            redundant_findings.extend(
                _process_disable_directive(
                    directive,
                    source,
                    currently_disabled,
                    redundant_disables,
                    supp_02_enabled=supp_02_enabled,
                )
            )
        elif directive.action == "enable":
            new_spans, new_findings = _process_enable_directive(
                directive,
                source,
                currently_disabled,
                supp_02_enabled=supp_02_enabled,
            )
            spans.extend(new_spans)
            redundant_findings.extend(new_findings)

    text_len = len(source.text) + 1
    for rule_id, prev_directive in currently_disabled.items():
        spans.append(_DisableSpan(prev_directive, rule_id, prev_directive.offset, text_len))

    return spans, redundant_findings, redundant_disables


def _filter_and_track(
    source: Source,
    findings: Iterable[Finding],
    same_line_ignores: dict[int, set[str]],
    spans: Sequence[_DisableSpan],
    ignored_set: frozenset[str],
) -> tuple[list[Finding], set[tuple[int, str]], set[tuple[Directive, str]]]:
    """Filter findings against same-line and range suppressions while tracking usage."""
    kept: list[Finding] = []
    used_ignores: set[tuple[int, str]] = set()
    used_disables: set[tuple[Directive, str]] = set()

    for finding in findings:
        if finding.rule_id in ignored_set:
            continue
        if finding.rule_id in same_line_ignores.get(finding.line, ()):
            used_ignores.add((finding.line, finding.rule_id))
            continue

        finding_offset = source.offset_of(finding.line, finding.column)
        suppressing_directive = None
        for span in spans:
            if span.rule_id == finding.rule_id and span.start <= finding_offset < span.end:
                if span.directive.offset == finding_offset:
                    continue
                suppressing_directive = span.directive
                break

        if suppressing_directive is not None:
            used_disables.add((suppressing_directive, finding.rule_id))
        else:
            kept.append(finding)

    return kept, used_ignores, used_disables


def _unused_ignore_findings(
    source: Source,
    directive: Directive,
    state: _SuppressionState,
    *,
    for_meta: bool,
) -> list[Finding]:
    """Report unused rule suppressions on an ignore directive."""
    findings = []
    for rule_id in sorted(directive.rule_ids):
        if rule_id in state.ignored_set or for_meta != (rule_id in _META_RULES):
            continue
        if (directive.line, rule_id) not in state.used_ignores:
            correction = (
                f"Remove '{rule_id}' from the directive."
                if len(directive.rule_ids) > 1
                else f"Remove '{rule_id}' from the directive, or remove the entire directive."
            )
            findings.append(
                source.finding(
                    directive.offset,
                    "SUPP-01",
                    f"unused suppression for rule '{rule_id}'",
                    correction,
                )
            )
    return findings


def _unused_disable_findings(
    source: Source,
    directive: Directive,
    state: _SuppressionState,
    *,
    for_meta: bool,
) -> list[Finding]:
    """Report unused rule suppressions on a disable directive."""
    findings = []
    for rule_id in sorted(directive.rule_ids):
        if rule_id in state.ignored_set or for_meta != (rule_id in _META_RULES):
            continue
        if (directive, rule_id) in state.redundant_disables:
            continue
        if (directive, rule_id) not in state.used_disables:
            correction = (
                f"Remove '{rule_id}' from the disable directive."
                if len(directive.rule_ids) > 1
                else f"Remove '{rule_id}' from the disable directive, or remove the entire directive."
            )
            findings.append(
                source.finding(
                    directive.offset,
                    "SUPP-01",
                    f"unused suppression for rule '{rule_id}'",
                    correction,
                )
            )
    return findings


def _detect_unused_suppressions(
    source: Source,
    directives: Sequence[Directive],
    state: _SuppressionState,
    *,
    for_meta: bool,
) -> list[Finding]:
    """Generate findings for directives that did not suppress any violation."""
    if "SUPP-01" in state.ignored_set:
        return []

    unused_findings: list[Finding] = []
    for directive in directives:
        if directive.action == "ignore":
            unused_findings.extend(_unused_ignore_findings(source, directive, state, for_meta=for_meta))
        elif directive.action == "disable":
            unused_findings.extend(_unused_disable_findings(source, directive, state, for_meta=for_meta))

    return unused_findings


def filter_findings(
    source: Source,
    findings: Iterable[Finding],
    directives: Sequence[Directive],
    ignored_rules: Collection[str] | None = None,
) -> list[Finding]:
    """Filter findings and emit unused or redundant suppression directives."""
    ignored_set = frozenset(ignored_rules) if ignored_rules else frozenset()
    same_line_ignores: dict[int, set[str]] = {}
    for directive in directives:
        if directive.action == "ignore":
            same_line_ignores.setdefault(directive.line, set()).update(directive.rule_ids)

    spans, redundant_findings, redundant_disables = _analyze_state_directives(source, directives, ignored_set)

    kept, used_ignores, used_disables = _filter_and_track(source, findings, same_line_ignores, spans, ignored_set)

    initial_state = _SuppressionState(used_ignores, used_disables, redundant_disables, ignored_set)
    unused_non_meta = _detect_unused_suppressions(
        source,
        directives,
        initial_state,
        for_meta=False,
    )

    candidate_meta = [*redundant_findings, *unused_non_meta]
    kept_meta, meta_used_ignores, meta_used_disables = _filter_and_track(
        source, candidate_meta, same_line_ignores, spans, ignored_set
    )

    meta_state = _SuppressionState(
        used_ignores | meta_used_ignores,
        used_disables | meta_used_disables,
        redundant_disables,
        ignored_set,
    )
    unused_meta = _detect_unused_suppressions(
        source,
        directives,
        meta_state,
        for_meta=True,
    )
    kept_unused_meta, _, _ = _filter_and_track(source, unused_meta, same_line_ignores, spans, ignored_set)

    kept.extend(kept_meta)
    kept.extend(kept_unused_meta)
    return kept
