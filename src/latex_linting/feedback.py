import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document, DocumentNode
from latex_linting.scanner import Token
from latex_linting.source import Source

_DIRECTIVE_RE = re.compile(r"^latex-lint\s*:\s*(?:ignore|disable|enable)(?:=.*)?$", re.IGNORECASE)
_CITE_RE = re.compile(r"^(?:cite-checked|citation-checked)(?:\s*:.*)?$", re.IGNORECASE)
_MAGIC_RE = re.compile(r"^!\s*TEX\s+", re.IGNORECASE)
_SECTION_CMD_RE = re.compile(r"\\(?:part|chapter|section|subsection|subsubsection|paragraph|subparagraph)\*?(?![a-zA-Z])")
_LABEL_CMD_RE = re.compile(r"^\s*\\label\{[^}]*\}\s*(?:%.*)?$")
_BLANK_LINE_RE = re.compile(r"^\s*$")
_PREAMBLE_CMD_RE = re.compile(r"^\s*\\(?:documentclass|usepackage|begin\{document\}|end\{document\})(?![a-zA-Z])")


@dataclass(frozen=True)
class _FeedbackEntry:
    """Store feedback output lines together with their character offset for document ordering."""

    offset: int
    lines: tuple[str, ...]


@dataclass
class _ParseState:
    """Track structural hierarchy and preceding paragraph state across source lines."""

    last_section_line: tuple[int, str] | None = None
    text_since_section: bool = False
    current_paragraph: list[tuple[int, str]] = field(default_factory=list)
    last_paragraph: list[tuple[int, str]] = field(default_factory=list)


def is_feedback_comment(comment_text: str) -> bool:
    """Check whether a comment token contains actionable feedback rather than directives or blanks."""
    stripped = comment_text.strip("%").strip()
    if not stripped or _MAGIC_RE.match(stripped):
        return False
    parts = comment_text.lstrip("%").split("%")
    for part in parts:
        item = part.strip()
        if not item or _DIRECTIVE_RE.match(item) or _CITE_RE.match(item):
            continue
        return True
    return False


def _resolve_context(state: _ParseState) -> list[tuple[int, str]]:
    """Determine the context lines for a standalone feedback comment block."""
    if state.last_section_line is not None and not state.text_since_section:
        return [state.last_section_line]
    if state.current_paragraph:
        return list(state.current_paragraph)
    if state.last_paragraph:
        return list(state.last_paragraph)
    return []


def _process_standalone_block(
    source: Source,
    lines: list[str],
    comments: dict[int, Token],
    start_line: int,
    state: _ParseState,
) -> tuple[int, _FeedbackEntry | None]:
    """Process a contiguous block of standalone comment lines, returning next line index and entry."""
    line_starts = source._line_starts  # noqa: SLF001 -- internal line offset index
    block_end = start_line
    total = len(lines)
    while block_end <= total:
        tok = comments.get(block_end)
        if tok is None or source.text[line_starts[block_end - 1] : tok.start].strip() != "":
            break
        block_end += 1

    feedback_lines = [
        (idx, lines[idx - 1])
        for idx in range(start_line, block_end)
        if is_feedback_comment(comments[idx].value)
    ]
    if not feedback_lines:
        return block_end, None

    context = _resolve_context(state)
    formatted = tuple(f"{source.filename}:{lno}: {txt}" for lno, txt in (*context, *feedback_lines))
    entry = _FeedbackEntry(line_starts[start_line - 1], formatted)
    if state.current_paragraph:
        state.last_paragraph = list(state.current_paragraph)
        state.current_paragraph = []
    return block_end, entry


def _process_inline_comment(
    source: Source,
    line_idx: int,
    line_text: str,
    comment_tok: Token,
    state: _ParseState,
) -> _FeedbackEntry | None:
    """Process a line containing an inline comment, updating paragraph and section state."""
    l_offset = source._line_starts[line_idx - 1]  # noqa: SLF001 -- internal line offset index
    entry = None
    if is_feedback_comment(comment_tok.value):
        entry = _FeedbackEntry(l_offset, (f"{source.filename}:{line_idx}: {line_text}",))

    before_comment = source.text[l_offset : comment_tok.start]
    if _SECTION_CMD_RE.search(before_comment):
        state.last_section_line = (line_idx, line_text)
        state.text_since_section = False
        state.current_paragraph = []
        state.last_paragraph = []
    else:
        state.text_since_section = True
        state.current_paragraph.append((line_idx, line_text))
    return entry


def _process_text_line(line_idx: int, line_text: str, state: _ParseState) -> None:
    """Update paragraph and section tracking state for a non-comment line."""
    if _BLANK_LINE_RE.match(line_text):
        if state.current_paragraph:
            state.last_paragraph = list(state.current_paragraph)
            state.current_paragraph = []
        return

    if _PREAMBLE_CMD_RE.search(line_text):
        state.current_paragraph = []
        state.last_paragraph = []
        state.last_section_line = None
        state.text_since_section = False
        return

    if _SECTION_CMD_RE.search(line_text):
        state.last_section_line = (line_idx, line_text)
        state.text_since_section = False
        state.current_paragraph = []
        state.last_paragraph = []
        return

    if not state.text_since_section and _LABEL_CMD_RE.match(line_text):
        return

    state.text_since_section = True
    state.current_paragraph.append((line_idx, line_text))


def _collect_source_entries(source: Source, tokens: tuple[Token, ...]) -> list[_FeedbackEntry]:
    """Extract feedback entries and context lines from a single source file."""
    lines = source.text.splitlines()
    comments = {source.line_number(tok.start): tok for tok in tokens if tok.kind == "comment"}

    entries: list[_FeedbackEntry] = []
    state = _ParseState()
    line_idx = 1
    total_lines = len(lines)

    while line_idx <= total_lines:
        tok = comments.get(line_idx)
        if tok is not None and source.text[source._line_starts[line_idx - 1] : tok.start].strip() == "":  # noqa: SLF001 -- internal line offset index
            line_idx, entry = _process_standalone_block(source, lines, comments, line_idx, state)
            if entry is not None:
                entries.append(entry)
            continue

        line_text = lines[line_idx - 1]
        if tok is not None:
            inline_entry = _process_inline_comment(source, line_idx, line_text, tok, state)
            if inline_entry is not None:
                entries.append(inline_entry)
        else:
            _process_text_line(line_idx, line_text, state)
        line_idx += 1

    return entries


def _extract_node_feedback(node: "DocumentNode") -> list[str]:
    """Recursively extract feedback lines from a document node, interleaving child includes."""
    entries = _collect_source_entries(node.source, node.tokens)
    result: list[str] = []
    entry_idx = 0

    for cmd, child in node.children:
        while entry_idx < len(entries) and entries[entry_idx].offset < cmd.start:
            result.extend(entries[entry_idx].lines)
            entry_idx += 1
        result.extend(_extract_node_feedback(child))

    while entry_idx < len(entries):
        result.extend(entries[entry_idx].lines)
        entry_idx += 1

    return result


def extract_feedback_lines(document: "Document") -> list[str]:
    """Return all formatted feedback lines in document reading order."""
    if document.root_node.source.filename.endswith(".bib"):
        return []
    return _extract_node_feedback(document.root_node)
