import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.scanner import Token, scan
from latex_linting.source import Source

_TABLE_FLOAT_ENVIRONMENTS = frozenset({"table", "table*"})
_TABULAR_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "tabulary", "longtable"})
_WIDTH_TABULAR_ENVIRONMENTS = frozenset({"tabular*", "tabularx", "tabulary"})


@dataclass(frozen=True)
class CaptionInfo:
    """Store extracted caption command token, argument text, and float-level status."""

    command_token: Token
    text: str
    is_float_level: bool


@dataclass(frozen=True)
class LabelInfo:
    """Store extracted label command token, target key, and inside-caption status."""

    command_token: Token
    target: str
    is_inside_caption: bool


@dataclass(frozen=True)
class TabularInfo:
    """Store tabular environment metadata, column rule violations, and forbidden rules."""

    source: Source
    begin_token: Token
    end_token: Token | None
    env_name: str
    pipe_offsets: tuple[int, ...]
    forbidden_rules: tuple[Token, ...]


@dataclass(frozen=True)
class TableFloat:
    """Retain structural elements of a table or table* float environment."""

    source: Source
    begin_token: Token
    end_token: Token | None
    env_name: str
    tabular_tokens: tuple[Token, ...]
    captions: tuple[CaptionInfo, ...]
    labels: tuple[LabelInfo, ...]
    center_env_tokens: tuple[Token, ...]
    forbidden_rules: tuple[Token, ...]
    has_centering: bool


def _skip_ignorable(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past whitespace and comments."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _skip_optional_bracket(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past optional bracket argument if present."""
    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.lstrip().startswith("["):
        depth = 0
        while idx < len(tokens):
            if tokens[idx].kind != "comment":
                for char in tokens[idx].value:
                    if char == "[":
                        depth += 1
                    elif char == "]":
                        depth -= 1
            idx += 1
            if depth <= 0:
                break
    return idx


def _extract_braced_argument(tokens: Sequence[Token], cmd_idx: int) -> tuple[str, int]:
    """Extract braced argument text following a command, skipping comments and whitespace."""
    idx = _skip_ignorable(tokens, cmd_idx + 1)
    idx = _skip_ignorable(tokens, _skip_optional_bracket(tokens, idx))
    if idx >= len(tokens) or tokens[idx].kind != "brace" or tokens[idx].value != "{":
        return "", idx
    brace_depth = 1
    idx += 1
    parts: list[str] = []
    while idx < len(tokens) and brace_depth > 0:
        cur = tokens[idx]
        if cur.kind == "brace":
            brace_depth += 1 if cur.value == "{" else -1
        if brace_depth > 0 and cur.kind != "comment":
            parts.append(cur.value)
        idx += 1
    return "".join(parts).strip(), idx


def _extract_braced_tokens(tokens: Sequence[Token], idx: int) -> tuple[list[Token], int]:
    """Extract tokens enclosed by matching curly braces, returning inner tokens and next index."""
    idx = _skip_ignorable(tokens, idx)
    if idx >= len(tokens) or tokens[idx].kind != "brace" or tokens[idx].value != "{":
        return [], idx
    brace_depth = 1
    idx += 1
    inner: list[Token] = []
    while idx < len(tokens) and brace_depth > 0:
        cur = tokens[idx]
        if cur.kind == "brace":
            brace_depth += 1 if cur.value == "{" else -1
        if brace_depth > 0:
            inner.append(cur)
        idx += 1
    return inner, idx


def _find_pipe_offsets(tokens: Sequence[Token]) -> tuple[int, ...]:
    """Find character offsets of all vertical rules '|' in column specification tokens."""
    offsets: list[int] = []
    for tok in tokens:
        if tok.kind == "text":
            offsets.extend(tok.start + match.start() for match in re.finditer(r"\|", tok.value))
    return tuple(offsets)


def _parse_tabular_args(
    tokens: Sequence[Token],
    start_idx: int,
    env_name: str,
) -> tuple[tuple[int, ...], int]:
    """Parse tabular arguments after begin token and return pipe offsets and body index."""
    idx = _skip_ignorable(tokens, start_idx)

    if env_name in _WIDTH_TABULAR_ENVIRONMENTS:
        _, idx = _extract_braced_tokens(tokens, idx)
        idx = _skip_ignorable(tokens, idx)

    idx = _skip_optional_bracket(tokens, idx)
    idx = _skip_ignorable(tokens, idx)

    cols_tokens, idx = _extract_braced_tokens(tokens, idx)
    pipe_offsets = _find_pipe_offsets(cols_tokens)
    return pipe_offsets, idx


def _parse_caption(
    tokens: Sequence[Token],
    cmd_idx: int,
    *,
    is_float_level: bool,
) -> tuple[CaptionInfo | None, list[LabelInfo], int]:
    """Parse caption command arguments, extracting caption text and nested labels."""
    idx = _skip_ignorable(tokens, cmd_idx + 1)
    idx = _skip_ignorable(tokens, _skip_optional_bracket(tokens, idx))
    if idx >= len(tokens) or tokens[idx].kind != "brace" or tokens[idx].value != "{":
        return None, [], idx

    brace_depth = 1
    idx += 1
    inner_tokens: list[Token] = []
    while idx < len(tokens) and brace_depth > 0:
        cur = tokens[idx]
        if cur.kind == "brace":
            brace_depth += 1 if cur.value == "{" else -1
        if brace_depth > 0:
            inner_tokens.append(cur)
        idx += 1

    nested_labels: list[LabelInfo] = []
    text_parts: list[str] = []
    inner_idx = 0
    while inner_idx < len(inner_tokens):
        cur = inner_tokens[inner_idx]
        if cur.kind == "comment":
            inner_idx += 1
            continue
        if cur.kind == "command" and cur.value == r"\label":
            target, next_inner = _extract_braced_argument(inner_tokens, inner_idx)
            if target:
                nested_labels.append(LabelInfo(cur, target, is_inside_caption=True))
            inner_idx = next_inner
            continue
        text_parts.append(cur.value)
        inner_idx += 1

    caption_text = "".join(text_parts).strip()
    caption_info = CaptionInfo(tokens[cmd_idx], caption_text, is_float_level)
    return caption_info, nested_labels, idx


class _FloatBuilder:
    """Accumulate elements of an active table float."""

    def __init__(self, source: Source, begin_token: Token, env_name: str) -> None:
        self.source = source
        self.begin_token = begin_token
        self.end_token: Token | None = None
        self.env_name = env_name
        self.tabular_tokens: list[Token] = []
        self.captions: list[CaptionInfo] = []
        self.labels: list[LabelInfo] = []
        self.center_env_tokens: list[Token] = []
        self.forbidden_rules: list[Token] = []
        self.has_centering = False

    def build(self) -> TableFloat:
        """Convert accumulated components into an immutable TableFloat."""
        return TableFloat(
            source=self.source,
            begin_token=self.begin_token,
            end_token=self.end_token,
            env_name=self.env_name,
            tabular_tokens=tuple(self.tabular_tokens),
            captions=tuple(self.captions),
            labels=tuple(self.labels),
            center_env_tokens=tuple(self.center_env_tokens),
            forbidden_rules=tuple(self.forbidden_rules),
            has_centering=self.has_centering,
        )


class _TabularBuilder:
    """Accumulate elements of an active tabular environment."""

    def __init__(
        self,
        source: Source,
        begin_token: Token,
        env_name: str,
        pipe_offsets: tuple[int, ...],
    ) -> None:
        self.source = source
        self.begin_token = begin_token
        self.end_token: Token | None = None
        self.env_name = env_name
        self.pipe_offsets = pipe_offsets
        self.forbidden_rules: list[Token] = []

    def build(self) -> TabularInfo:
        """Convert accumulated components into an immutable TabularInfo."""
        return TabularInfo(
            source=self.source,
            begin_token=self.begin_token,
            end_token=self.end_token,
            env_name=self.env_name,
            pipe_offsets=self.pipe_offsets,
            forbidden_rules=tuple(self.forbidden_rules),
        )


class _SourceTableScanner:
    """Scan tokens of a single source file to extract table floats and tabular environments."""

    def __init__(self, source: Source, tokens: Sequence[Token]) -> None:
        self.source = source
        self.tokens = tokens
        self.floats: list[TableFloat] = []
        self.tabulars: list[TabularInfo] = []
        self.active_floats: list[_FloatBuilder] = []
        self.active_tabulars: list[_TabularBuilder] = []

    def _handle_environment(self, token: Token, idx: int) -> int:
        """Process environment begin or end token, returning next token index."""
        name = token.value[token.value.index("{") + 1 : -1]
        is_begin = token.value.startswith(r"\begin")

        if is_begin:
            if name in _TABLE_FLOAT_ENVIRONMENTS:
                self.active_floats.append(_FloatBuilder(self.source, token, name))
                return idx + 1
            if name == "center":
                if self.active_floats:
                    self.active_floats[-1].center_env_tokens.append(token)
                return idx + 1
            if name in _TABULAR_ENVIRONMENTS:
                if self.active_floats:
                    self.active_floats[-1].tabular_tokens.append(token)
                pipe_offsets, next_idx = _parse_tabular_args(self.tokens, idx + 1, name)
                self.active_tabulars.append(_TabularBuilder(self.source, token, name, pipe_offsets))
                return next_idx
        else:
            if name in _TABLE_FLOAT_ENVIRONMENTS and self.active_floats and self.active_floats[-1].env_name == name:
                builder = self.active_floats.pop()
                builder.end_token = token
                self.floats.append(builder.build())
                return idx + 1
            if name in _TABULAR_ENVIRONMENTS and self.active_tabulars and self.active_tabulars[-1].env_name == name:
                builder = self.active_tabulars.pop()
                builder.end_token = token
                self.tabulars.append(builder.build())
                return idx + 1

        return idx + 1

    def _handle_command(self, token: Token, idx: int) -> int:
        """Process command token within table floats or tabular environments."""
        cmd = token.value

        if cmd in (r"\hline", r"\cline"):
            if self.active_tabulars:
                self.active_tabulars[-1].forbidden_rules.append(token)
            elif self.active_floats:
                self.active_floats[-1].forbidden_rules.append(token)
            return idx + 1

        if self.active_floats:
            if cmd == r"\centering":
                self.active_floats[-1].has_centering = True
                return idx + 1
            if cmd == r"\caption":
                caption_info, nested_labels, next_idx = _parse_caption(self.tokens, idx, is_float_level=True)
                if caption_info is not None:
                    self.active_floats[-1].captions.append(caption_info)
                self.active_floats[-1].labels.extend(nested_labels)
                return next_idx
            if cmd == r"\label":
                target, next_idx = _extract_braced_argument(self.tokens, idx)
                if target:
                    self.active_floats[-1].labels.append(LabelInfo(token, target, is_inside_caption=False))
                return next_idx

        return idx + 1

    def scan(self) -> tuple[list[TableFloat], list[TabularInfo]]:
        """Execute token scan and return collected table floats and tabular environments."""
        idx = 0
        while idx < len(self.tokens):
            token = self.tokens[idx]
            if token.kind in ("comment", "literal"):
                idx += 1
            elif token.kind == "environment":
                idx = self._handle_environment(token, idx)
            elif token.kind == "command":
                idx = self._handle_command(token, idx)
            else:
                idx += 1

        while self.active_tabulars:
            self.tabulars.append(self.active_tabulars.pop().build())

        while self.active_floats:
            self.floats.append(self.active_floats.pop().build())

        return self.floats, self.tabulars


def collect_document_tables(document: "Document") -> tuple[list[TableFloat], list[TabularInfo]]:
    """Collect all table floats and tabular environments across document sources."""
    all_floats: list[TableFloat] = []
    all_tabulars: list[TabularInfo] = []
    for source in document.sources:
        floats, tabulars = _SourceTableScanner(source, scan(source.text)).scan()
        all_floats.extend(floats)
        all_tabulars.extend(tabulars)
    return all_floats, all_tabulars
