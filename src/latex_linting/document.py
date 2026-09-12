from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.rules.model import Rule
from latex_linting.rules.catalogue import RULES
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source
from latex_linting.suppression import Directive, filter_findings, parse_directives


class MissingIncludeError(FileNotFoundError):
    """Describe a failure to resolve an included LaTeX source file."""

    def __init__(self, filename: str, line: int, target: str) -> None:
        super().__init__(f"{filename}:{line}: cannot find included file '{target}'")
        self.filename = filename
        self.line = line
        self.target = target

    def __str__(self) -> str:
        """Return the formatted include failure message."""
        return f"{self.filename}:{self.line}: cannot find included file '{self.target}'"


@dataclass(frozen=True)
class IncludeCommand:
    """Describe a literal input or include command in a source."""

    command: str
    target: str
    start: int
    end: int
    line: int


@dataclass(frozen=True)
class DocumentNode:
    """Represent a source file and its child includes in the document hierarchy."""

    source: Source
    tokens: tuple[Token, ...]
    directives: tuple[Directive, ...]
    children: tuple[tuple[IncludeCommand, "DocumentNode"], ...]


@dataclass(frozen=True)
class Document:
    """Represent a loaded LaTeX document tree and its source collection."""

    root_node: DocumentNode
    sources: tuple[Source, ...]
    bib_nodes: tuple[DocumentNode, ...] = ()

    def traverse(self) -> Iterable[tuple[Source, Token]]:
        """Yield tokens and their originating source in document reading order."""
        if self.root_node.source.filename.endswith(".bib"):
            return ()
        return _traverse_node(self.root_node)


def _find_candidate_file(candidate: Path) -> Path | None:
    """Return the candidate if it is a file, trying .tex extension if omitted."""
    if candidate.is_file():
        return candidate
    if candidate.suffix != ".tex":
        tex_path = Path(str(candidate) + ".tex")
        if tex_path.is_file():
            return tex_path
    return None


def resolve_include_path(target_str: str, including_path: Path, root_dir: Path) -> Path | None:
    """Resolve an include target to a filesystem path relative to the file or root."""
    target = target_str.strip()
    if not target or target.startswith("\\"):
        return None
    target_path = Path(target)
    if target_path.is_absolute():
        return _find_candidate_file(target_path)

    base_dir = including_path.parent
    directories = [base_dir]
    if base_dir.resolve() != root_dir.resolve():
        directories.append(root_dir)

    for directory in directories:
        found = _find_candidate_file(directory / target_path)
        if found is not None:
            return found
    return None


def _find_candidate_bib_file(candidate: Path) -> Path | None:
    """Return the candidate if it is a file, trying .bib extension if omitted."""
    if candidate.is_file():
        return candidate
    if candidate.suffix != ".bib":
        bib_path = Path(str(candidate) + ".bib")
        if bib_path.is_file():
            return bib_path
    return None


def resolve_bib_path(target_str: str, including_path: Path, root_dir: Path) -> Path | None:
    """Resolve a bibliography target to a filesystem path relative to the file or root."""
    target = target_str.strip()
    if not target or target.startswith(("\\", "http://", "https://")):
        return None
    target_path = Path(target)
    if target_path.is_absolute():
        return _find_candidate_bib_file(target_path)

    base_dir = including_path.parent
    directories = [base_dir]
    if base_dir.resolve() != root_dir.resolve():
        directories.append(root_dir)

    for directory in directories:
        found = _find_candidate_bib_file(directory / target_path)
        if found is not None:
            return found
    return None


def _parse_include_target(tokens: Sequence[Token], start_idx: int) -> tuple[str, int, int]:
    """Parse the include target and return target string, end offset, and next token index."""
    target_idx = start_idx
    while target_idx < len(tokens) and (
        tokens[target_idx].kind == "comment"
        or (tokens[target_idx].kind == "text" and tokens[target_idx].value.isspace())
    ):
        target_idx += 1

    if target_idx >= len(tokens):
        return "", -1, target_idx

    next_token = tokens[target_idx]
    if next_token.kind == "brace" and next_token.value == "{":
        brace_depth = 1
        content_idx = target_idx + 1
        target_parts: list[str] = []
        while content_idx < len(tokens) and brace_depth > 0:
            cur = tokens[content_idx]
            if cur.kind == "brace":
                brace_depth += 1 if cur.value == "{" else -1
            if brace_depth > 0 and cur.kind != "comment":
                target_parts.append(cur.value)
            content_idx += 1

        if brace_depth > 0:
            return "".join(target_parts).strip(), -1, content_idx

        target = "".join(target_parts).strip()
        return target, tokens[content_idx - 1].end, content_idx

    if next_token.kind == "text":
        val = next_token.value.lstrip()
        word = val.split()[0] if val.split() else ""
        return word.strip(), next_token.end, target_idx + 1

    return next_token.value.strip(), next_token.end, target_idx + 1


def _find_includes(source: Source, tokens: Sequence[Token]) -> list[IncludeCommand]:
    """Identify literal input and include commands in scanned tokens."""
    includes: list[IncludeCommand] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind != "command" or token.value not in (r"\input", r"\include"):
            idx += 1
            continue

        line = source.line_number(token.start)
        cmd = token.value
        cmd_start = token.start
        target, cmd_end, idx = _parse_include_target(tokens, idx + 1)
        if cmd_end == -1:
            raise MissingIncludeError(source.filename, line, target)

        includes.append(IncludeCommand(cmd, target, cmd_start, cmd_end, line))

    return includes


def _parse_bib_targets(tokens: Sequence[Token], start_idx: int) -> tuple[list[str], int, int]:
    """Parse bibliography targets from command tokens, returning targets, end offset, next idx."""
    idx = start_idx
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1

    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.startswith("["):
        bracket_depth = 0
        while idx < len(tokens):
            val = tokens[idx].value
            bracket_depth += val.count("[") - val.count("]")
            idx += 1
            if bracket_depth <= 0:
                break
        while idx < len(tokens) and (
            tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
        ):
            idx += 1

    target_str, end_offset, next_idx = _parse_include_target(tokens, idx)
    if end_offset == -1:
        return [target_str] if target_str else [], -1, next_idx
    targets = [t.strip() for t in target_str.split(",") if t.strip()]
    return targets, end_offset, next_idx


def _find_bib_commands(source: Source, tokens: Sequence[Token]) -> list[tuple[str, int]]:
    """Identify targets and lines of bibliography commands in scanned tokens."""
    bib_entries: list[tuple[str, int]] = []
    idx = 0
    bib_commands = frozenset({r"\addbibresource", r"\bibliography", r"\addglobalbib"})
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind != "command" or token.value not in bib_commands:
            idx += 1
            continue

        line = source.line_number(token.start)
        targets, cmd_end, idx = _parse_bib_targets(tokens, idx + 1)
        if cmd_end == -1:
            raw_target = targets[0] if targets else ""
            raise MissingIncludeError(source.filename, line, raw_target)

        bib_entries.extend((target, line) for target in targets)
    return bib_entries


def _load_bib_node(path: Path, filename: str) -> DocumentNode:
    """Read one bibliography file, scan its tokens, and parse directives."""
    with path.open(encoding="utf-8", newline="") as handle:
        source = Source(filename, handle.read())
    tokens = scan(source.text)
    directives = parse_directives(source, tokens)
    return DocumentNode(source, tokens, directives, ())


@dataclass
class _LoadContext:
    """Retain document load state across recursive inclusion passes."""

    root_dir: Path
    loaded_sources: list[Source]
    bib_nodes: list[DocumentNode]
    loaded_bib_paths: set[Path]


def _load_node(
    path: Path,
    filename: str,
    active_chain: tuple[Path, ...],
    ctx: _LoadContext,
) -> DocumentNode:
    """Read one source file, scan tokens, load child includes, and collect bibliography nodes."""
    with path.open(encoding="utf-8", newline="") as handle:
        source = Source(filename, handle.read())
    ctx.loaded_sources.append(source)
    tokens = scan(source.text)
    directives = parse_directives(source, tokens)
    include_cmds = _find_includes(source, tokens)
    children: list[tuple[IncludeCommand, DocumentNode]] = []
    canonical = path.resolve()
    new_chain = (*active_chain, canonical)

    for cmd in include_cmds:
        target_path = resolve_include_path(cmd.target, path, ctx.root_dir)
        if target_path is None:
            raise MissingIncludeError(source.filename, cmd.line, cmd.target)
        if target_path.resolve() in new_chain:
            msg = f"{source.filename}:{cmd.line}: circular inclusion of '{cmd.target}'"
            raise ValueError(msg)
        child_node = _load_node(target_path, str(target_path), new_chain, ctx)
        children.append((cmd, child_node))

    bib_entries = _find_bib_commands(source, tokens)
    for target, line in bib_entries:
        target_path = resolve_bib_path(target, path, ctx.root_dir)
        if target_path is None:
            raise MissingIncludeError(source.filename, line, target)
        canonical_bib = target_path.resolve()
        if canonical_bib not in ctx.loaded_bib_paths:
            ctx.loaded_bib_paths.add(canonical_bib)
            ctx.bib_nodes.append(_load_bib_node(target_path, str(target_path)))

    return DocumentNode(source, tokens, directives, tuple(children))


def load_document(root: str | Path) -> Document:
    """Load root document and recursively follow input, include, and bibliography commands."""
    root_path = Path(root)
    if root_path.suffix == ".bib":
        bib_node = _load_bib_node(root_path, str(root))
        return Document(bib_node, (), (bib_node,))

    ctx = _LoadContext(root_path.parent, [], [], set())
    root_node = _load_node(root_path, str(root), (), ctx)
    return Document(root_node, tuple(ctx.loaded_sources), tuple(ctx.bib_nodes))


def _traverse_node(node: DocumentNode) -> Iterable[tuple[Source, Token]]:
    """Yield tokens and their originating source in document reading order."""
    token_idx = 0
    tokens = node.tokens
    for cmd, child in node.children:
        while token_idx < len(tokens) and tokens[token_idx].end <= cmd.start:
            yield node.source, tokens[token_idx]
            token_idx += 1
        while token_idx < len(tokens) and tokens[token_idx].start < cmd.end:
            token_idx += 1
        yield from _traverse_node(child)
    while token_idx < len(tokens):
        yield node.source, tokens[token_idx]
        token_idx += 1


def ordered_findings(
    document: Document,
    ignored_rules: Collection[str] | None = None,
    rule_filter: Collection[str] | None = None,
    enabled_rules: Collection[str] | None = None,
) -> list[Finding]:
    """Collect and order findings across a document, included children, and bibliography files."""
    ignored_set = frozenset(ignored_rules) if ignored_rules is not None else frozenset()
    filter_set = frozenset(rule_filter) if rule_filter is not None else None
    enabled_set = frozenset(enabled_rules) if enabled_rules is not None else frozenset()

    rules_to_run: list[Rule] = []
    for rule in RULES:
        if filter_set is not None:
            if rule.rule_id in filter_set and rule.rule_id not in ignored_set:
                rules_to_run.append(rule)
        else:
            is_active = rule.enabled_by_default or (rule.rule_id in enabled_set)
            if is_active and rule.rule_id not in ignored_set:
                rules_to_run.append(rule)

    all_findings: list[Finding] = []
    for rule in rules_to_run:
        all_findings.extend(rule.evaluate(document))

    findings_by_file: dict[str, list[Finding]] = {}
    for finding in all_findings:
        findings_by_file.setdefault(finding.filename, []).append(finding)

    active_ids = {r.rule_id for r in rules_to_run}
    all_rule_ids = {r.rule_id for r in RULES}
    effective_ignored = (all_rule_ids - active_ids) | ignored_set

    findings: list[Finding] = []
    if not document.root_node.source.filename.endswith(".bib"):
        findings.extend(_collect_node_findings(document.root_node, findings_by_file, effective_ignored))

    for bib_node in document.bib_nodes:
        file_findings = findings_by_file.get(bib_node.source.filename, [])
        filtered = filter_findings(bib_node.source, file_findings, bib_node.directives, effective_ignored)
        sorted_filtered = sorted(filtered, key=lambda f: (f.line, f.column, f.rule_id))
        findings.extend(sorted_filtered)

    if filter_set is not None:
        findings = [f for f in findings if f.rule_id in filter_set]

    return findings


def _collect_node_findings(
    node: DocumentNode,
    findings_by_file: dict[str, list[Finding]],
    ignored_rules: Collection[str] | None,
) -> list[Finding]:
    """Collect filtered findings for a node and recursively interleave child includes."""
    file_findings = findings_by_file.get(node.source.filename, [])
    filtered = filter_findings(node.source, file_findings, node.directives, ignored_rules)
    sorted_filtered = sorted(filtered, key=lambda f: (f.line, f.column, f.rule_id))

    findings: list[Finding] = []
    finding_idx = 0
    for cmd, child in node.children:
        while finding_idx < len(sorted_filtered):
            f = sorted_filtered[finding_idx]
            f_offset = node.source.offset_of(f.line, f.column)
            if f_offset < cmd.start:
                findings.append(f)
                finding_idx += 1
            else:
                break
        findings.extend(_collect_node_findings(child, findings_by_file, ignored_rules))

    while finding_idx < len(sorted_filtered):
        findings.append(sorted_filtered[finding_idx])
        finding_idx += 1

    return findings
