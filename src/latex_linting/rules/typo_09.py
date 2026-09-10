from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_ALL_STANDARD_PREFIXES = (
    "ch:",
    "cha:",
    "sec:",
    "fig:",
    "tab:",
    "eq:",
    "app:",
    "lst:",
    "listing:",
)

_FIGURE_ENVIRONMENTS = frozenset({"figure", "figure*"})
_TABLE_ENVIRONMENTS = frozenset({"table", "table*"})
_MATH_ENVIRONMENTS = frozenset(
    {
        "align",
        "align*",
        "alignat",
        "alignat*",
        "displaymath",
        "equation",
        "equation*",
        "eqnarray",
        "eqnarray*",
        "flalign",
        "flalign*",
        "gather",
        "gather*",
        "multline",
        "multline*",
    }
)

_SECTION_COMMANDS = frozenset({r"\section", r"\subsection", r"\subsubsection"})

_CONTEXT_SPECS: dict[str, tuple[tuple[str, ...], str, str]] = {
    "figure": (
        ("fig:",),
        "Label inside figure environment must use prefix 'fig:'.",
        "Change label prefix to 'fig:'.",
    ),
    "table": (
        ("tab:",),
        "Label inside table environment must use prefix 'tab:'.",
        "Change label prefix to 'tab:'.",
    ),
    "math": (
        ("eq:",),
        "Label inside math environment must use prefix 'eq:'.",
        "Change label prefix to 'eq:'.",
    ),
    "chapter": (
        ("ch:", "cha:", "app:"),
        "Label for chapter must use prefix 'ch:'.",
        "Change label prefix to 'ch:' (or 'cha:').",
    ),
    "section": (
        ("sec:", "app:"),
        "Label for section must use prefix 'sec:'.",
        "Change label prefix to 'sec:'.",
    ),
    "unknown": (
        _ALL_STANDARD_PREFIXES,
        "Label uses nonstandard prefix; standard prefixes are 'ch:', 'sec:', 'fig:', 'tab:', 'eq:', 'app:', 'lst:'.",
        "Use a standard label prefix such as 'ch:', 'sec:', 'fig:', 'tab:', 'eq:', 'app:', or 'lst:'.",
    ),
}


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
        while idx < len(tokens):
            if "]" in tokens[idx].value:
                return idx + 1
            idx += 1
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


def _scan_heading_label(
    tokens: Sequence[Token],
    start_idx: int,
    heading_type: str,
    heading_labels: dict[int, str],
) -> int:
    """Consume a heading's arguments and associate immediately attached labels."""
    idx = _skip_ignorable(tokens, start_idx)
    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.lstrip().startswith("*"):
        idx = _skip_ignorable(tokens, idx + 1)

    idx = _skip_ignorable(tokens, _skip_optional_bracket(tokens, idx))

    if idx < len(tokens) and tokens[idx].kind == "brace" and tokens[idx].value == "{":
        brace_depth = 1
        idx += 1
        while idx < len(tokens) and brace_depth > 0:
            cur = tokens[idx]
            if cur.kind == "brace":
                brace_depth += 1 if cur.value == "{" else -1
            elif cur.kind == "command" and cur.value == r"\label":
                heading_labels[cur.start] = heading_type
            idx += 1

    post_idx = _skip_ignorable(tokens, idx)
    if post_idx < len(tokens) and tokens[post_idx].kind == "command" and tokens[post_idx].value == r"\label":
        heading_labels[tokens[post_idx].start] = heading_type
        return post_idx + 1

    return idx


def _find_heading_attached_labels(tokens: Sequence[Token]) -> dict[int, str]:
    r"""Map offsets of \label commands attached to headings to 'chapter' or 'section'."""
    heading_labels: dict[int, str] = {}
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind == "command" and (token.value == r"\chapter" or token.value in _SECTION_COMMANDS):
            heading_type = "chapter" if token.value == r"\chapter" else "section"
            idx = _scan_heading_label(tokens, idx + 1, heading_type, heading_labels)
        else:
            idx += 1
    return heading_labels


def _determine_context(
    env_stack: list[str],
    token: Token,
    heading_labels: dict[int, str],
) -> str:
    """Classify the structural context surrounding a label command."""
    if any(env in _FIGURE_ENVIRONMENTS for env in env_stack):
        return "figure"
    if any(env in _TABLE_ENVIRONMENTS for env in env_stack):
        return "table"
    if any(env in _MATH_ENVIRONMENTS for env in env_stack) or token.math == "display":
        return "math"
    if token.start in heading_labels:
        return heading_labels[token.start]
    return "unknown"


def _validate_label(
    source: Source,
    token: Token,
    target: str,
    context: str,
) -> Finding | None:
    """Check label target against required prefix for its context."""
    prefixes, explanation, correction = _CONTEXT_SPECS[context]
    if not target.startswith(prefixes):
        return source.finding(token.start, RULE.rule_id, explanation, correction)
    return None


def _check_source_labels(source: Source) -> Iterable[Finding]:
    """Scan a source file for label prefix violations based on context."""
    tokens = scan(source.text)
    heading_labels = _find_heading_attached_labels(tokens)
    env_stack: list[str] = []

    for idx, token in enumerate(tokens):
        if token.kind == "environment":
            name = token.value[token.value.index("{") + 1 : -1]
            if token.value.startswith(r"\begin"):
                env_stack.append(name)
            elif token.value.startswith(r"\end") and env_stack and env_stack[-1] == name:
                env_stack.pop()
            continue

        if token.kind == "command" and token.value == r"\label":
            target, _ = _extract_braced_argument(tokens, idx)
            if target:
                context = _determine_context(env_stack, token, heading_labels)
                finding = _validate_label(source, token, target, context)
                if finding is not None:
                    yield finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate label prefixes across all sources in the document."""
    for source in document.sources:
        yield from _check_source_labels(source)


RULE = Rule(
    rule_id="TYPO-09",
    explanation="Label must use a standard prefix corresponding to its category or context.",
    correction=(
        "Use standard label prefixes: 'ch:' for chapters, 'sec:' for sections, 'fig:' for figures, "
        "'tab:' for tables, 'eq:' for equations, 'app:' for appendices, 'lst:' for listings."
    ),
    passing_examples=(
        "\\section{Methods}\n\\label{sec:methods}",
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Overview.}\n"
            "  \\label{fig:overview}\n"
            "\\end{figure}\n"
            "See Figure~\\ref{fig:overview} for details."
        ),
        (
            "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:einstein}\n\\end{equation}\n"
            "As seen in~\\eqref{eq:einstein}, mass and energy are equivalent."
        ),
    ),
    failing_examples=(
        "\\section{Methods}\n\\label{methods}",
        "\\begin{figure}\n  \\caption{Overview}\n  \\label{diagram}\n\\end{figure}",
        "\\begin{figure}\n  \\caption{Overview}\n  \\label{sec:figure}\n\\end{figure}",
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{formula}\n\\end{equation}",
    ),
    limits=(
        "Checks label prefixes in \\label commands against known contexts: figures (figure, figure*) "
        "require 'fig:', tables (table, table*) require 'tab:', display math environments require 'eq:', "
        "headings immediately preceding require 'ch:' or 'cha:' (chapters) or 'sec:' (sections, "
        "subsections, subsubsections). In unknown contexts outside these environments and headings, "
        "labels must start with one of the standard prefixes ('ch:', 'cha:', 'sec:', 'fig:', 'tab:', "
        "'eq:', 'app:', 'lst:', 'listing:'). Labels in comments or literal code are excluded."
    ),
    evaluate=_evaluate,
)
