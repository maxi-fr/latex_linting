from bisect import bisect_right
from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Finding:
    """Describe a violation at a one-based position in the original source."""

    rule_id: str
    filename: str
    line: int
    column: int
    excerpt: str
    explanation: str
    correction: str
    severity: Severity = "error"


@dataclass(frozen=True)
class Source:
    """Keep source text and its line index together without rewriting either."""

    filename: str
    text: str
    _line_starts: tuple[int, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Index line starts once for all findings in this file."""
        starts = (0, *(offset + 1 for offset, char in enumerate(self.text) if char == "\n"))
        object.__setattr__(self, "_line_starts", starts)

    def line_number(self, offset: int) -> int:
        """Return the one-based line number for a character offset."""
        return bisect_right(self._line_starts, offset)

    def offset_of(self, line: int, column: int) -> int:
        """Return the zero-based character offset for a one-based line and column."""
        return self._line_starts[line - 1] + (column - 1)

    def finding(
        self,
        offset: int,
        rule_id: str,
        explanation: str,
        correction: str,
        severity: Severity = "error",
    ) -> Finding:
        """Locate a rule violation using an offset into the original text, assigning severity."""
        line = self.line_number(offset)
        start = self._line_starts[line - 1]
        end = self.text.find("\n", start)
        excerpt = self.text[start : end if end != -1 else len(self.text)].rstrip("\r")
        return Finding(
            rule_id=rule_id,
            filename=self.filename,
            line=line,
            column=offset - start + 1,
            excerpt=excerpt,
            explanation=explanation,
            correction=correction,
            severity=severity,
        )
