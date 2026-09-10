from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_DISPLAY_ENVIRONMENTS = frozenset(
    {
        "displaymath",
        "equation",
        "equation*",
        "align",
        "align*",
        "alignat",
        "alignat*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "flalign",
        "flalign*",
        "eqnarray",
        "eqnarray*",
    }
)


def _is_display_open(token: Token) -> str | None:
    """Return the display environment or delimiter name if token opens display math."""
    if token.kind == "command" and token.value == r"\[":
        return r"\]"
    if token.kind == "delimiter" and token.value == "$$":
        return "$$"
    if token.kind == "environment" and token.value.startswith(r"\begin"):
        name = token.value[token.value.index("{") + 1 : -1]
        if name in _DISPLAY_ENVIRONMENTS:
            return r"\end{" + name + "}"
    return None


def _check_source_blank_lines(source: Source) -> Iterable[Finding]:
    """Scan a source for genuinely blank lines inside supported math environments."""
    tokens = scan(source.text)
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        close_target = _is_display_open(token)
        if close_target is None:
            idx += 1
            continue

        open_line = source.line_number(token.start)
        close_token: Token | None = None
        idx += 1
        while idx < len(tokens):
            cur = tokens[idx]
            if (
                close_target in {r"\]", "$$"} and cur.kind in {"command", "delimiter"} and cur.value == close_target
            ) or (close_target.startswith(r"\end") and cur.kind == "environment" and cur.value == close_target):
                close_token = cur
                idx += 1
                break
            idx += 1

        if close_token is not None:
            close_line = source.line_number(close_token.start)
            for line_num in range(open_line + 1, close_line):
                start = source.offset_of(line_num, 1)
                end = source.text.find("\n", start)
                line_content = source.text[start : end if end != -1 else len(source.text)].rstrip("\r\n")
                if not line_content.strip():
                    yield source.finding(start, RULE.rule_id, RULE.explanation, RULE.correction)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report genuinely blank lines inside supported math environments across the document."""
    for source in document.sources:
        yield from _check_source_blank_lines(source)


RULE = Rule(
    rule_id="MATH-13",
    explanation="Do not place blank lines inside math environments; use comment lines (%) for visual spacing.",
    correction="Remove the blank line or replace it with a comment line starting with %.",
    passing_examples=(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}",
        "\\begin{align}\n  a &= b \\,,\n  % separation\n  c &= d \\,.\n\\end{align}",
    ),
    failing_examples=(
        "\\begin{equation}\n  a = b \\,,\n\n  c = d \\,.\n\\end{equation}",
        "\\[\n  a = b \\,,\n\n  c = d \\,.\n\\]",
    ),
    limits=(
        "Detects genuinely blank lines (containing only whitespace) inside supported display math "
        "environments (equation, align, gather, multline, alignat, flalign, eqnarray, their starred forms, "
        "displaymath, \\[...\\], and $$...$$). Comment-only lines starting with % are permitted and not flagged. "
        "Reports the blank line at column 1. Does not check inline math ($...$ or \\(...\\))."
    ),
    evaluate=_evaluate,
)
