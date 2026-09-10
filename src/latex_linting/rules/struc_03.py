from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_HEADING_LEVELS: dict[str, int] = {
    r"\part": 0,
    r"\chapter": 1,
    r"\section": 2,
    r"\subsection": 3,
    r"\subsubsection": 4,
    r"\paragraph": 5,
    r"\subparagraph": 6,
}


@dataclass
class _HeadingNode:
    """Record an active heading and its direct children grouped by level."""

    source: Source
    token: Token
    level: int
    children_by_level: dict[int, list["_HeadingNode"]]


def _check_isolated(parent: _HeadingNode, findings: list[Finding]) -> None:
    """Flag any child level of parent that has exactly one numbered child."""
    for children in parent.children_by_level.values():
        if len(children) == 1:
            child = children[0]
            findings.append(
                child.source.finding(
                    child.token.start,
                    RULE.rule_id,
                    RULE.explanation,
                    RULE.correction,
                )
            )


def _isolated_subheadings(document: "Document") -> Iterable[Finding]:
    """Report isolated subheadings across the loaded document."""
    findings: list[Finding] = []
    stack: list[_HeadingNode] = []
    brace_depth = 0

    for source, token in document.traverse():
        if token.kind == "brace":
            if token.value == "{":
                brace_depth += 1
            elif token.value == "}":
                brace_depth = max(0, brace_depth - 1)
            continue

        if token.kind != "command" or token.math != "text" or brace_depth != 0 or token.value not in _HEADING_LEVELS:
            continue

        level = _HEADING_LEVELS[token.value]
        rest = source.text[token.end :].lstrip(" \t\r\n")
        is_starred = rest.startswith("*")

        while stack and stack[-1].level >= level:
            popped = stack.pop()
            _check_isolated(popped, findings)

        if is_starred:
            continue

        node = _HeadingNode(source, token, level, {})
        if stack:
            parent = stack[-1]
            parent.children_by_level.setdefault(level, []).append(node)
        stack.append(node)

    while stack:
        popped = stack.pop()
        _check_isolated(popped, findings)

    return findings


RULE = Rule(
    rule_id="STRUC-03",
    explanation="Subheadings must have at least two sibling headings at the same level; isolated subheadings are forbidden.",
    correction="Add at least one more sibling subheading at this level, or incorporate the content into the parent section without a subheading.",
    passing_examples=(
        "\\section{First}\n\\subsection{Sub A}\n\\subsection{Sub B}",
        "\\chapter{Chapter One}\n\\section{Section 1.1}\n\\section{Section 1.2}",
    ),
    failing_examples=(
        "\\section{First}\n\\subsection{Only Subheading}",
        "\\chapter{Chapter One}\n\\section{Only Section}",
    ),
    limits=(
        r"Checks numbered LaTeX headings (\part, \chapter, \section, \subsection, etc.) "
        "across the document in reading order, including across included files. "
        "Starred headings are unnumbered and do not participate in hierarchy counting. "
        "Comments, literal code blocks, and headings inside command arguments are excluded. "
        "Findings are attached to the isolated child heading command backslash to enable same-line ignore directives."
    ),
    evaluate=_isolated_subheadings,
)
