import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_NON_PROSE_ENVIRONMENTS = frozenset(
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
        "itemize",
        "enumerate",
        "description",
        "figure",
        "figure*",
        "table",
        "table*",
        "tabular",
        "tabular*",
        "tabularx",
        "tabulary",
        "longtable",
    }
)

_FLOATING_ENVIRONMENTS = frozenset({"figure", "figure*", "table", "table*"})
_HEADING_COMMANDS = frozenset({r"\chapter", r"\section", r"\subsection", r"\subsubsection", r"\addchap", r"\addsec"})
_DIVISION_COMMANDS = frozenset({r"\frontmatter", r"\mainmatter", r"\backmatter", r"\appendix"})
_REFERENCE_KEYWORDS = frozenset({"symbol", "acronym", "notation", "abbreviation", "nomenclature"})

_NON_PROSE_COMMANDS = frozenset(
    {
        r"\clearpage",
        r"\newpage",
        r"\pagebreak",
        r"\nopagebreak",
        r"\bigskip",
        r"\medskip",
        r"\smallskip",
        r"\noindent",
        r"\FloatBarrier",
        r"\relax",
        r"\centering",
        r"\raggedright",
        r"\raggedleft",
    }
)


@dataclass
class _TraverseState:
    """Retain section context and candidate ending block during document traversal."""

    candidate: tuple[Source, Token] | None = None
    in_section: bool = False
    has_prose: bool = False
    in_frontmatter: bool = False
    in_appendix: bool = False
    non_prose_stack: list[str] = field(default_factory=list)
    in_bracket_math: bool = False
    in_dollar_math: bool = False

    @property
    def in_non_prose_block(self) -> bool:
        """Return True if currently inside any recognized non-prose environment or display math."""
        return bool(self.non_prose_stack) or self.in_bracket_math or self.in_dollar_math


def _skip_whitespace_and_comments(tokens: tuple[tuple[Source, Token], ...], start_idx: int) -> int:
    """Skip over whitespace and comment tokens starting from start_idx."""
    idx = start_idx
    while idx < len(tokens) and (
        tokens[idx][1].kind == "comment" or (tokens[idx][1].kind == "text" and tokens[idx][1].value.isspace())
    ):
        idx += 1
    return idx


def _skip_braces(tokens: tuple[tuple[Source, Token], ...], start_idx: int) -> int:
    """Skip over matching curly braces, returning the index after the closing brace."""
    idx = _skip_whitespace_and_comments(tokens, start_idx)
    if idx < len(tokens) and tokens[idx][1].kind == "brace" and tokens[idx][1].value == "{":
        depth = 1
        idx += 1
        while idx < len(tokens) and depth > 0:
            cur = tokens[idx][1]
            if cur.kind == "brace":
                depth += 1 if cur.value == "{" else -1
            idx += 1
    return idx


def _skip_brackets(tokens: tuple[tuple[Source, Token], ...], start_idx: int) -> int:
    """Skip over optional brackets [...], returning the index after the closing bracket."""
    idx = _skip_whitespace_and_comments(tokens, start_idx)
    if idx < len(tokens) and tokens[idx][1].kind == "text" and tokens[idx][1].value.lstrip().startswith("["):
        while idx < len(tokens):
            if "]" in tokens[idx][1].value:
                idx += 1
                break
            idx += 1
    return idx


def _extract_heading_info(tokens: tuple[tuple[Source, Token], ...], start_idx: int) -> tuple[bool, str, int]:
    """Extract whether a heading is starred, its title text, and the next token index."""
    idx = _skip_whitespace_and_comments(tokens, start_idx)
    is_starred = False
    if idx < len(tokens) and tokens[idx][1].kind == "text" and tokens[idx][1].value.startswith("*"):
        is_starred = True
        idx += 1
    idx = _skip_brackets(tokens, idx)
    idx = _skip_whitespace_and_comments(tokens, idx)
    title_parts: list[str] = []
    if idx < len(tokens) and tokens[idx][1].kind == "brace" and tokens[idx][1].value == "{":
        depth = 1
        idx += 1
        while idx < len(tokens) and depth > 0:
            cur = tokens[idx][1]
            if cur.kind == "brace":
                depth += 1 if cur.value == "{" else -1
            if depth > 0 and cur.kind != "comment":
                title_parts.append(cur.value)
            idx += 1
    return is_starred, "".join(title_parts).strip(), idx


def _is_exempt_heading(state: _TraverseState, cmd: str, *, is_starred: bool, title: str) -> bool:
    """Check if a heading is exempt from prose termination rules."""
    if state.in_frontmatter or state.in_appendix:
        return True
    if is_starred or cmd in {r"\addchap", r"\addsec"}:
        return True
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in _REFERENCE_KEYWORDS)


def _handle_division_command(state: _TraverseState, token: Token, findings: list[Finding]) -> None:
    """Update document division state upon frontmatter, mainmatter, or appendix commands."""
    if state.candidate is not None:
        findings.append(
            state.candidate[0].finding(state.candidate[1].start, RULE.rule_id, RULE.explanation, RULE.correction)
        )
        state.candidate = None
    if token.value == r"\frontmatter":
        state.in_frontmatter = True
    elif token.value == r"\mainmatter":
        state.in_frontmatter = False
    elif token.value in (r"\backmatter", r"\appendix"):
        state.in_appendix = True
        state.in_frontmatter = False
    state.in_section = False
    state.has_prose = False


def _handle_heading_command(
    state: _TraverseState, tokens: tuple[tuple[Source, Token], ...], idx: int, findings: list[Finding]
) -> int:
    """Process sectioning heading, report preceding violations, and update section state."""
    token = tokens[idx][1]
    if state.candidate is not None:
        findings.append(
            state.candidate[0].finding(state.candidate[1].start, RULE.rule_id, RULE.explanation, RULE.correction)
        )
        state.candidate = None
    is_starred, title, next_idx = _extract_heading_info(tokens, idx + 1)
    if _is_exempt_heading(state, token.value, is_starred=is_starred, title=title):
        state.in_section = False
    else:
        state.in_section = True
    state.has_prose = False
    return next_idx


def _handle_environment(state: _TraverseState, source: Source, token: Token, findings: list[Finding]) -> None:
    """Update non-prose environment stack and candidate state upon begin/end tokens."""
    name = token.value[token.value.index("{") + 1 : -1]
    if token.value.startswith(r"\begin"):
        if name in _NON_PROSE_ENVIRONMENTS:
            state.non_prose_stack.append(name)
    elif token.value.startswith(r"\end"):
        if name == "document":
            if state.candidate is not None:
                findings.append(
                    state.candidate[0].finding(
                        state.candidate[1].start, RULE.rule_id, RULE.explanation, RULE.correction
                    )
                )
                state.candidate = None
            state.in_section = False
        elif state.non_prose_stack and state.non_prose_stack[-1] == name:
            state.non_prose_stack.pop()
            if not state.non_prose_stack and state.in_section:
                if name in _FLOATING_ENVIRONMENTS:
                    if not state.has_prose and state.candidate is None:
                        state.candidate = (source, token)
                else:
                    state.candidate = (source, token)


def _handle_delimiters(state: _TraverseState, source: Source, token: Token) -> bool:
    """Handle bracket or double-dollar display math delimiters; return True if handled."""
    if token.kind == "command" and token.value == r"\[":
        state.in_bracket_math = True
        return True
    if token.kind == "command" and token.value == r"\]":
        state.in_bracket_math = False
        if state.in_section:
            state.candidate = (source, token)
        return True
    if token.kind == "delimiter" and token.value == "$$":
        state.in_dollar_math = not state.in_dollar_math
        if not state.in_dollar_math and state.in_section:
            state.candidate = (source, token)
        return True
    return False


def _handle_prose_command(state: _TraverseState, tokens: tuple[tuple[Source, Token], ...], idx: int) -> int:
    """Handle command tokens in potential prose context, returning updated index."""
    token = tokens[idx][1]
    if token.value in {r"\label", r"\vspace", r"\vspace*", r"\hspace", r"\hspace*"}:
        return _skip_braces(tokens, idx + 1)
    if token.value not in _NON_PROSE_COMMANDS and token.value not in {r"\input", r"\include"}:
        state.candidate = None
        state.has_prose = True
    return idx + 1


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report sections ending directly on an equation, list, table, or figure."""
    tokens = tuple(document.traverse())
    state = _TraverseState()
    findings: list[Finding] = []

    idx = 0
    while idx < len(tokens):
        source, token = tokens[idx]

        if token.kind == "command" and token.value in _DIVISION_COMMANDS and token.math == "text":
            _handle_division_command(state, token, findings)
            idx += 1
            continue

        if token.kind == "command" and token.value in _HEADING_COMMANDS and token.math == "text":
            idx = _handle_heading_command(state, tokens, idx, findings)
            continue

        if token.kind == "environment":
            _handle_environment(state, source, token, findings)
            idx += 1
            continue

        if _handle_delimiters(state, source, token):
            idx += 1
            continue

        if state.in_non_prose_block or token.kind == "comment" or (token.kind == "text" and token.value.isspace()):
            idx += 1
            continue

        if token.kind == "command":
            idx = _handle_prose_command(state, tokens, idx)
            continue

        if token.kind == "delimiter" or (token.kind == "text" and re.search(r"\w", token.value)):
            state.candidate = None
            state.has_prose = True

        idx += 1

    if state.candidate is not None:
        findings.append(
            state.candidate[0].finding(state.candidate[1].start, RULE.rule_id, RULE.explanation, RULE.correction)
        )

    return findings


RULE = Rule(
    rule_id="STRUC-06",
    explanation="Sections and chapters must end on prose, not directly on an equation, list, table, or figure.",
    correction="Add a concluding sentence or paragraph after the block before ending the section or moving to the next heading.",
    passing_examples=(
        "\\section{Methods}\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\nThis relation governs our model.\n\\section{Results}",
        "\\subsection{Overview}\n\\begin{itemize}\n  \\item First item\n  \\item Second item\n\\end{itemize}\nThese items form the basis of our approach.",
    ),
    failing_examples=(
        "\\section{Methods}\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n\\section{Results}",
        "\\subsection{Overview}\n\\begin{figure}\n  \\caption{A figure.}\n\\end{figure}\n\\end{document}",
    ),
    limits=(
        "Detects chapters, sections, subsections, and subsubsections ending directly on a recognized "
        "display math equation, list (itemize, enumerate, description), table (table, tabular, tabularx, "
        "etc.), or figure environment before the next heading or document end. Whitespace, comments, "
        "trailing labels, and formatting commands (e.g. \\newpage, \\clearpage) do not count as prose. "
        "Floating environments (figure, table) trailing after prose in a section do not trigger violations. "
        "Frontmatter, appendix, unnumbered headings, and reference/symbol list sections are exempt. "
        "A prose continuation in an included file satisfies the rule. Does not check whether the final "
        "prose is grammatically complete or a well-formed sentence."
    ),
    evaluate=_evaluate,
)
