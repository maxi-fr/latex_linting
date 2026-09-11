from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.scanner import Token, scan
from latex_linting.source import Source

_REFERENCE_COMMANDS = frozenset({r"\ref", r"\autoref", r"\cref", r"\Cref"})
_FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*"})


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
class FigureFloat:
    """Retain structural elements of a figure or figure* float environment."""

    source: Source
    begin_token: Token
    end_token: Token | None
    env_name: str
    image_tokens: tuple[Token, ...]
    captions: tuple[CaptionInfo, ...]
    labels: tuple[LabelInfo, ...]
    center_env_tokens: tuple[Token, ...]
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
    """Accumulate components of an open figure float during token scanning."""

    def __init__(self, source: Source, begin_token: Token, env_name: str) -> None:
        self.source = source
        self.begin_token = begin_token
        self.end_token: Token | None = None
        self.env_name = env_name
        self.image_tokens: list[Token] = []
        self.captions: list[CaptionInfo] = []
        self.labels: list[LabelInfo] = []
        self.center_env_tokens: list[Token] = []
        self.has_centering = False

    def build(self) -> FigureFloat:
        """Convert accumulated components into an immutable FigureFloat."""
        return FigureFloat(
            source=self.source,
            begin_token=self.begin_token,
            end_token=self.end_token,
            env_name=self.env_name,
            image_tokens=tuple(self.image_tokens),
            captions=tuple(self.captions),
            labels=tuple(self.labels),
            center_env_tokens=tuple(self.center_env_tokens),
            has_centering=self.has_centering,
        )


_TITLE_OR_METADATA_COMMANDS = frozenset(
    {
        r"\title",
        r"\subtitle",
        r"\author",
        r"\institute",
        r"\date",
        r"\titlehead",
        r"\subject",
        r"\publishers",
        r"\uppertitleback",
        r"\lowertitleback",
        r"\dedication",
        r"\extratitle",
        r"\reviewer",
        r"\supervisor",
        r"\advisor",
        r"\committee",
        r"\submissiondate",
        r"\department",
        r"\addTitleBox",
        r"\savebox",
        r"\sbox",
        r"\parbox",
        r"\makebox",
        r"\mbox",
        r"\framebox",
        r"\newsavebox",
        r"\fancyhead",
        r"\fancyfoot",
        r"\ihead",
        r"\ohead",
        r"\chead",
        r"\cfoot",
        r"\ofoot",
        r"\ifoot",
    }
)
_TWO_ARG_BOX_COMMANDS = frozenset({r"\savebox", r"\sbox", r"\parbox"})


class _SourceFigureScanner:
    """Scan tokens of a single source file to extract figure floats and outside images."""

    def __init__(self, source: Source, tokens: Sequence[Token]) -> None:
        """Initialize figure float scanner with source, tokens, and metadata context tracking."""
        self.source = source
        self.tokens = tokens
        self.floats: list[FigureFloat] = []
        self.outside_images: list[tuple[Source, Token]] = []
        self.env_stack: list[str] = []
        self.current_builder: _FloatBuilder | None = None
        self.has_begin_document = any(t.kind == "environment" and t.value == r"\begin{document}" for t in tokens)
        self.in_preamble = self.has_begin_document
        self.box_depth = 0
        self.pending_box_args = 0
        self.expecting_box_brace = False

    @property
    def in_figure_float(self) -> bool:
        """Return True if currently inside a figure or figure* environment."""
        return any(env in _FIGURE_ENVIRONMENTS for env in self.env_stack)

    @property
    def in_exempt_graphic_context(self) -> bool:
        """Return True if currently inside preamble, titlepage, or title/box macro."""
        return self.in_preamble or self.box_depth > 0 or "titlepage" in self.env_stack

    def _handle_begin(self, name: str, token: Token) -> None:
        """Process environment opening tokens and track document, float, or graphic environments."""
        if name == "document":
            self.in_preamble = False
        if name in _FIGURE_ENVIRONMENTS:
            if not self.in_figure_float:
                self.current_builder = _FloatBuilder(self.source, token, name)
        elif name == "center":
            if self.current_builder is not None:
                self.current_builder.center_env_tokens.append(token)
        elif name == "tikzpicture":
            if not self.in_figure_float and not self.in_exempt_graphic_context:
                self.outside_images.append((self.source, token))
            elif self.current_builder is not None:
                self.current_builder.image_tokens.append(token)
        self.env_stack.append(name)

    def _handle_end(self, name: str, token: Token) -> None:
        """Process an environment closing token."""
        if name in _FIGURE_ENVIRONMENTS and self.current_builder is not None and self.current_builder.env_name == name:
            self.current_builder.end_token = token
            self.floats.append(self.current_builder.build())
            self.current_builder = None
        while self.env_stack and self.env_stack[-1] != name:
            self.env_stack.pop()
        if self.env_stack:
            self.env_stack.pop()

    def _handle_environment(self, token: Token) -> None:
        """Dispatch environment token to begin or end handlers."""
        name = token.value[token.value.index("{") + 1 : -1]
        if token.value.startswith(r"\begin"):
            self._handle_begin(name, token)
        elif token.value.startswith(r"\end"):
            self._handle_end(name, token)

    def _handle_float_command(self, cmd: str, token: Token, idx: int) -> int:
        """Process commands specific to an active figure float."""
        if self.current_builder is None:
            return idx + 1

        if cmd in (r"\input", r"\include"):
            self.current_builder.image_tokens.append(token)
            _, next_idx = _extract_braced_argument(self.tokens, idx)
            return next_idx

        if cmd == r"\centering":
            self.current_builder.has_centering = True
            return idx + 1

        if cmd == r"\caption":
            is_float_level = self.env_stack in (["figure"], ["figure*"])
            caption_info, nested_labels, next_idx = _parse_caption(self.tokens, idx, is_float_level=is_float_level)
            if caption_info is not None:
                self.current_builder.captions.append(caption_info)
            self.current_builder.labels.extend(nested_labels)
            return next_idx

        if cmd == r"\label":
            target, next_idx = _extract_braced_argument(self.tokens, idx)
            if target:
                self.current_builder.labels.append(LabelInfo(token, target, is_inside_caption=False))
            return next_idx

        return idx + 1

    def _handle_command(self, token: Token, idx: int) -> int:
        """Process command tokens for metadata boxes, active floats, or outside graphics."""
        cmd = token.value
        if cmd in _TITLE_OR_METADATA_COMMANDS:
            self.pending_box_args = 2 if cmd in _TWO_ARG_BOX_COMMANDS else 1
            self.expecting_box_brace = True

        if cmd == r"\includegraphics":
            if not self.in_figure_float and not self.in_exempt_graphic_context:
                self.outside_images.append((self.source, token))
            elif self.current_builder is not None:
                self.current_builder.image_tokens.append(token)
            return idx + 1

        return self._handle_float_command(cmd, token, idx)

    def _handle_text(self, token: Token) -> None:
        """Consume text and validate pending metadata box brace expectations."""
        if self.expecting_box_brace:
            stripped = token.value.strip()
            if not (token.value.isspace() or stripped.startswith(("*", "["))):
                self.expecting_box_brace = False
                self.pending_box_args = 0

    def _handle_brace(self, token: Token) -> None:
        """Update box nesting depth and consume expected box arguments on braces."""
        if token.value == "{":
            if self.expecting_box_brace:
                self.box_depth += 1
                self.expecting_box_brace = False
                self.pending_box_args = max(0, self.pending_box_args - 1)
            elif self.box_depth > 0:
                self.box_depth += 1
        elif token.value == "}" and self.box_depth > 0:
            self.box_depth -= 1
            if self.box_depth == 0 and self.pending_box_args > 0:
                self.expecting_box_brace = True

    def scan(self) -> tuple[list[FigureFloat], list[tuple[Source, Token]]]:
        """Execute token scan, tracking figure floats, outside images, and metadata contexts."""
        idx = 0
        while idx < len(self.tokens):
            token = self.tokens[idx]
            if token.kind in ("comment", "literal"):
                idx += 1
            elif token.kind == "environment":
                self._handle_environment(token)
                idx += 1
            elif token.kind == "command":
                idx = self._handle_command(token, idx)
            elif token.kind == "text":
                self._handle_text(token)
                idx += 1
            elif token.kind == "brace":
                self._handle_brace(token)
                idx += 1
            else:
                idx += 1

        if self.current_builder is not None:
            self.floats.append(self.current_builder.build())

        return self.floats, self.outside_images


def scan_source_figures(source: Source) -> tuple[list[FigureFloat], list[tuple[Source, Token]]]:
    """Extract figure floats and outside figure content from a source file."""
    return _SourceFigureScanner(source, scan(source.text)).scan()


def collect_document_references(document: "Document") -> set[str]:
    """Collect all label keys referenced by recognized figure reference commands across sources."""
    referenced: set[str] = set()
    for source in document.sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind == "command" and token.value in _REFERENCE_COMMANDS:
                arg, _ = _extract_braced_argument(tokens, idx)
                if arg:
                    for part in arg.split(","):
                        cleaned = part.strip()
                        if cleaned:
                            referenced.add(cleaned)
    return referenced


def collect_document_figures(
    document: "Document",
) -> tuple[list[FigureFloat], list[tuple[Source, Token]], Counter[str]]:
    """Collect all figure floats, outside image tokens, and document-wide label counts."""
    all_floats: list[FigureFloat] = []
    all_outside: list[tuple[Source, Token]] = []
    label_counts: Counter[str] = Counter()

    for source in document.sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind == "command" and token.value == r"\label":
                target, _ = _extract_braced_argument(tokens, idx)
                if target:
                    label_counts[target] += 1

        floats, outside = scan_source_figures(source)
        all_floats.extend(floats)
        all_outside.extend(outside)

    return all_floats, all_outside, label_counts
