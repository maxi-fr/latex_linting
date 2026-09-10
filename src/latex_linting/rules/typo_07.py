from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
    from latex_linting.scanner import Token
from latex_linting.rules.model import Rule
from latex_linting.source import Finding, Source

_TABLE_ENVIRONMENTS = frozenset({"tabular", "tabular*", "tabularx", "tabulary", "longtable"})
_HEADING_COMMANDS = frozenset(
    {
        r"\chapter",
        r"\chapter*",
        r"\section",
        r"\section*",
        r"\subsection",
        r"\subsection*",
        r"\subsubsection",
        r"\subsubsection*",
        r"\paragraph",
        r"\paragraph*",
        r"\subparagraph",
        r"\subparagraph*",
        r"\title",
    }
)
_EMPHASIS_COMMANDS = frozenset({r"\textbf", r"\textit", r"\emph", r"\textsl", r"\textsc", r"\underline"})


@dataclass
class _FontFrame:
    """Track an active font command, its origin, and nested status."""

    token: "Token"
    source: Source
    table_depth: int
    heading_depth: int
    has_nested: bool = False


class _EmphasisScanner:
    """Track font commands, headings, and table context across tokens."""

    def __init__(self) -> None:
        self.table_depth = 0
        self.heading_depth = 0
        self.expecting_heading_brace = False
        self.pending_font_cmd: Token | None = None
        self.pending_font_source: Source | None = None
        self.font_stack: list[_FontFrame] = []
        self.brace_kinds: list[str] = []

    def handle_environment(self, token: "Token") -> None:
        """Update table depth on entering or exiting tabular environments."""
        env_name = token.value[token.value.index("{") + 1 : -1]
        if token.value.startswith(r"\begin"):
            if env_name in _TABLE_ENVIRONMENTS:
                self.table_depth += 1
        elif token.value.startswith(r"\end") and env_name in _TABLE_ENVIRONMENTS:
            self.table_depth = max(0, self.table_depth - 1)
        self.pending_font_cmd = None
        self.pending_font_source = None

    def handle_command(self, source: Source, token: "Token") -> list[Finding]:
        """Check forbidden underline, combined attributes, and track pending commands."""
        findings: list[Finding] = []
        if token.math != "text":
            self.pending_font_cmd = None
            self.pending_font_source = None
            return findings

        if token.value in _HEADING_COMMANDS:
            self.expecting_heading_brace = True
            self.pending_font_cmd = None
            self.pending_font_source = None
            return findings

        if token.value == r"\underline":
            findings.append(
                source.finding(
                    token.start,
                    RULE.rule_id,
                    "Underlining ('\\underline{...}') is forbidden for emphasis in academic text.",
                    "Use '\\emph{...}' for single textual emphasis instead of '\\underline{...}'.",
                )
            )
            if self.font_stack:
                self.font_stack[-1].has_nested = True
                outer_cmd = self.font_stack[-1].token.value
                findings.append(
                    source.finding(
                        token.start,
                        RULE.rule_id,
                        f"Do not combine multiple font attributes ('\\underline' inside '{outer_cmd}'); "
                        "change only one attribute for emphasis.",
                        "Use '\\emph{...}' for single textual emphasis.",
                    )
                )
            self.pending_font_cmd = token
            self.pending_font_source = source
            return findings

        if token.value in _EMPHASIS_COMMANDS:
            if self.font_stack:
                self.font_stack[-1].has_nested = True
                outer_cmd = self.font_stack[-1].token.value
                findings.append(
                    source.finding(
                        token.start,
                        RULE.rule_id,
                        f"Do not combine multiple font attributes ('{token.value}' inside '{outer_cmd}'); "
                        "change only one attribute for emphasis.",
                        "Use '\\emph{...}' for single textual emphasis.",
                    )
                )
            self.pending_font_cmd = token
            self.pending_font_source = source
            return findings

        self.pending_font_cmd = None
        self.pending_font_source = None
        return findings

    def handle_text(self, token: "Token") -> None:
        """Handle intervening whitespace or brackets before braces."""
        if token.value.isspace():
            return
        if self.expecting_heading_brace and token.value.strip().startswith("["):
            return
        self.pending_font_cmd = None
        self.pending_font_source = None

    def handle_brace_open(self) -> None:
        """Push font frame or heading tracking on opening brace."""
        if self.pending_font_cmd is not None and self.pending_font_source is not None:
            self.font_stack.append(
                _FontFrame(
                    self.pending_font_cmd,
                    self.pending_font_source,
                    self.table_depth,
                    self.heading_depth,
                )
            )
            self.brace_kinds.append("font")
            self.pending_font_cmd = None
            self.pending_font_source = None
        elif self.expecting_heading_brace:
            self.brace_kinds.append("heading")
            self.heading_depth += 1
            self.expecting_heading_brace = False
        else:
            self.brace_kinds.append("other")
            if self.heading_depth > 0:
                self.heading_depth += 1

    def handle_brace_close(self) -> list[Finding]:
        """Pop brace scope and report standalone bold in running prose."""
        findings: list[Finding] = []
        self.pending_font_cmd = None
        self.pending_font_source = None
        if not self.brace_kinds:
            return findings

        kind = self.brace_kinds.pop()
        if kind == "font":
            frame = self.font_stack.pop()
            if (
                frame.token.value == r"\textbf"
                and not frame.has_nested
                and frame.table_depth == 0
                and frame.heading_depth == 0
            ):
                findings.append(
                    frame.source.finding(
                        frame.token.start,
                        RULE.rule_id,
                        "Bold ('\\textbf{...}') used as emphasis in running prose; "
                        "change only one font attribute and prefer integrated emphasis.",
                        "Use '\\emph{...}' for single textual emphasis instead of '\\textbf{...}'.",
                    )
                )
        elif kind == "heading":
            self.heading_depth = max(0, self.heading_depth - 1)
        elif kind == "other" and self.heading_depth > 0:
            self.heading_depth -= 1

        return findings


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document for forbidden underline, bold in running prose, and combined font attributes."""
    scanner = _EmphasisScanner()
    for source, token in document.traverse():
        if token.kind == "environment":
            scanner.handle_environment(token)
        elif token.kind == "command":
            yield from scanner.handle_command(source, token)
        elif token.kind == "text":
            scanner.handle_text(token)
        elif token.kind == "brace":
            if token.value == "{":
                scanner.handle_brace_open()
            elif token.value == "}":
                yield from scanner.handle_brace_close()


RULE = Rule(
    rule_id="TYPO-07",
    explanation="Forbidden emphasis command or combined font attributes.",
    correction="Use '\\emph{...}' for single textual emphasis.",
    passing_examples=(
        r"We use \emph{proper emphasis} in running text.",
        r"We can also use \textit{italicized terms} without combining.",
        r"\begin{tabular}{ll} \textbf{Parameter} & \textbf{Value} \\ \end{tabular}",
    ),
    failing_examples=(
        r"This is \underline{forbidden} styling.",
        r"We note that this result is \textbf{critically important}.",
        r"Combined \textbf{\textit{bold and italic}} text.",
        r"Combined \textbf{\emph{bold and emph}} text.",
    ),
    limits=(
        r"Detects '\underline{...}' anywhere in text mode, '\textbf{...}' used as emphasis in "
        r"running prose outside tables and headings, and nested/combined font attributes "
        r"('\textbf{\textit{...}}', '\textbf{\emph{...}}', '\emph{\textbf{...}}', '\underline{\emph{...}}'). "
        r"Bold formatting in table headers ('tabular', 'tabularx', etc.), single emphasis ('\emph{...}', "
        r"'\textit{...}'), math mode, comments, and literal environments are excluded."
    ),
    evaluate=_evaluate,
)
