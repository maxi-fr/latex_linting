from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
    from latex_linting.scanner import Token
from latex_linting.rules.model import Rule
from latex_linting.source import Finding, Source

_TABLE_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "tabulary", "longtable"})
_TITLE_AUTHOR_COMMANDS = frozenset({r"\title", r"\author", r"\subtitle", r"\institute", r"\date"})
_LINE_BREAK_COMMANDS = frozenset({r"\\", r"\newline", r"\linebreak"})


class _LineBreakScanner:
    """Track table context, title macros, and line breaks across document tokens."""

    def __init__(self) -> None:
        self.table_depth = 0
        self.title_depth = 0
        self.expecting_title_brace = False

    def handle_environment(self, token: "Token") -> None:
        """Update table depth when entering or leaving table environments."""
        env_name = token.value[token.value.index("{") + 1 : -1]
        if token.value.startswith(r"\begin"):
            if env_name in _TABLE_ENVIRONMENTS:
                self.table_depth += 1
        elif token.value.startswith(r"\end") and env_name in _TABLE_ENVIRONMENTS:
            self.table_depth = max(0, self.table_depth - 1)

    def handle_command(self, source: Source, token: "Token") -> Finding | None:
        """Check for forbidden line breaks in running text and track title macros."""
        if token.value in _TITLE_AUTHOR_COMMANDS:
            self.expecting_title_brace = True
            return None

        if (
            token.math == "text"
            and token.value in _LINE_BREAK_COMMANDS
            and self.table_depth == 0
            and self.title_depth == 0
        ):
            return source.finding(
                token.start,
                RULE.rule_id,
                f"Line-break command ('{token.value}') used as a paragraph break in running text.",
                f"Use a blank line in the source to start a new paragraph instead of '{token.value}'.",
            )

        return None

    def handle_text(self, token: "Token") -> None:
        """Consume whitespace or optional bracket arguments before title braces."""
        if not self.expecting_title_brace:
            return
        if token.value.isspace() or token.value.strip().startswith("["):
            return
        self.expecting_title_brace = False

    def handle_brace(self, token: "Token") -> None:
        """Update title macro nesting depth on opening or closing braces."""
        if token.value == "{":
            if self.expecting_title_brace:
                self.title_depth += 1
                self.expecting_title_brace = False
            elif self.title_depth > 0:
                self.title_depth += 1
        elif token.value == "}" and self.title_depth > 0:
            self.title_depth -= 1


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document for line-break commands used as paragraph breaks in running text."""
    scanner = _LineBreakScanner()
    for source, token in document.traverse():
        if token.kind == "environment":
            scanner.handle_environment(token)
        elif token.kind == "command":
            finding = scanner.handle_command(source, token)
            if finding is not None:
                yield finding
        elif token.kind == "text":
            scanner.handle_text(token)
        elif token.kind == "brace":
            scanner.handle_brace(token)


RULE = Rule(
    rule_id="TYPO-08",
    explanation="Line-break command used as a paragraph break in running text.",
    correction="Use a blank line in the source to start a new paragraph.",
    passing_examples=(
        "First paragraph of running text.\n\nSecond paragraph begins here.",
        "\\begin{tabular}{ll}\nA & B \\\\\nC & D \\\\\n\\end{tabular}",
        "\\begin{align}\nx &= 1 \\\\\ny &= 2 \\,.\n\\end{align}",
        "\\title{Thesis Title \\\\ Subtitle}",
        "\\author{First Author \\\\ Department of Engineering}",
    ),
    failing_examples=(
        "First paragraph of running text.\\\\\nSecond paragraph follows immediately.",
        "First paragraph of running text.\\newline\nSecond paragraph follows immediately.",
        "First paragraph of running text.\\linebreak\nSecond paragraph follows immediately.",
    ),
    limits=(
        r"Detects '\\', '\newline', and '\linebreak' in running text mode. Allows row breaks in "
        r"supported tables (tabular, tabular*, tabularx, tabulary, longtable), multiline math "
        r"(align, gather, equation, etc.), and title/author macros (\title, \author, \subtitle, "
        r"\institute, \date). Comments and literal environments are excluded."
    ),
    evaluate=_evaluate,
)
