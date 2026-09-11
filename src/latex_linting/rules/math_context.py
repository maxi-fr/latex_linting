from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.scanner import Token
from latex_linting.source import Source

_NON_MATH_COMMANDS = frozenset(
    {
        r"\text",
        r"\intertext",
        r"\shortintertext",
        r"\mbox",
        r"\textrm",
        r"\textbf",
        r"\textit",
        r"\textsf",
        r"\texttt",
        r"\textnormal",
        r"\textup",
        r"\textsl",
        r"\textsc",
        r"\tag",
        r"\label",
        r"\url",
        r"\href",
        r"\ref",
        r"\eqref",
        r"\cite",
        r"\autocite",
        r"\citep",
        r"\citet",
        r"\pageref",
    }
)

_UNIT_COMMANDS_SINGLE = frozenset({r"\unit", r"\si", r"\num"})
_UNIT_COMMANDS_DOUBLE = frozenset({r"\SI", r"\qty"})

_UPRIGHT_COMMANDS = frozenset(
    {
        r"\mathrm",
        r"\operatorname",
        r"\mathbf",
        r"\text",
        r"\textrm",
        r"\textbf",
    }
)


@dataclass(frozen=True)
class MathContext:
    """Retain classification of math mode, indices, and nested non-math or upright regions."""

    in_math: bool
    in_non_math: bool
    in_unit_command: bool
    in_upright: bool
    in_index: bool = False


class _DepthCounter:
    """Manage pending arguments and active nesting depth for a command category."""

    def __init__(self) -> None:
        self.pending = 0
        self.depth = 0

    def reset_pending(self) -> None:
        """Clear unconsumed argument expectations."""
        self.pending = 0

    def reset_all(self) -> None:
        """Reset both pending count and active depth."""
        self.pending = 0
        self.depth = 0

    def open_brace(self) -> None:
        """Handle opening brace by consuming a pending argument or incrementing depth."""
        if self.pending > 0:
            self.pending -= 1
            self.depth += 1
        elif self.depth > 0:
            self.depth += 1

    def close_brace(self) -> None:
        """Handle closing brace by decrementing active depth."""
        if self.depth > 0:
            self.depth -= 1


class ContextTracker:
    """Track math, non-math, unit, upright, and index nesting depths across tokens."""

    def __init__(self) -> None:
        self.non_math = _DepthCounter()
        self.unit = _DepthCounter()
        self.upright = _DepthCounter()
        self.index = _DepthCounter()

    def reset_all(self) -> None:
        """Reset all counters when outside math mode."""
        self.non_math.reset_all()
        self.unit.reset_all()
        self.upright.reset_all()
        self.index.reset_all()

    def _handle_command(self, cmd: str) -> None:
        """Register pending arguments for recognized commands."""
        self.non_math.reset_pending()
        self.unit.reset_pending()
        self.upright.reset_pending()
        if cmd in _NON_MATH_COMMANDS:
            self.non_math.pending = 2 if cmd == r"\href" else 1
        if cmd in _UNIT_COMMANDS_SINGLE:
            self.unit.pending = 1
        elif cmd in _UNIT_COMMANDS_DOUBLE:
            self.unit.pending = 2
        if cmd in _UPRIGHT_COMMANDS:
            self.upright.pending = 1

    def _handle_brace(self, brace: str) -> None:
        """Update active depths on braces."""
        if brace == "{":
            self.non_math.open_brace()
            self.unit.open_brace()
            self.upright.open_brace()
            self.index.open_brace()
        elif brace == "}":
            self.non_math.close_brace()
            self.unit.close_brace()
            self.upright.close_brace()
            self.index.close_brace()

    def handle_token(self, token: Token) -> None:
        """Update context counters based on the current token."""
        if token.kind == "command":
            self._handle_command(token.value)
            self.index.reset_pending()
        elif token.kind == "brace":
            self._handle_brace(token.value)
        elif token.kind == "text":
            stripped = token.value.rstrip()
            if stripped.endswith(("_", "^")):
                self.index.pending = 1
            elif not token.value.isspace():
                self.index.reset_pending()
            if not token.value.isspace():
                self.non_math.reset_pending()
                self.unit.reset_pending()
                self.upright.reset_pending()
        elif token.kind != "comment":
            self.non_math.reset_pending()
            self.unit.reset_pending()
            self.upright.reset_pending()
            self.index.reset_pending()

    def current_context(self, *, in_math: bool) -> MathContext:
        """Return the current context classification."""
        return MathContext(
            in_math=in_math,
            in_non_math=self.non_math.depth > 0,
            in_unit_command=self.unit.depth > 0,
            in_upright=self.upright.depth > 0,
            in_index=self.index.depth > 0,
        )


def iter_math_tokens(document: "Document") -> Iterable[tuple[Source, Token, MathContext]]:
    """Yield tokens with surrounding math, non-math, unit, and upright context."""
    tracker = ContextTracker()

    for source, token in document.traverse():
        in_math = token.math in ("inline", "display")
        if not in_math:
            tracker.reset_all()
            continue

        tracker.handle_token(token)
        yield source, token, tracker.current_context(in_math=in_math)
