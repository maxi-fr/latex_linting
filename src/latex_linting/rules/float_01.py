import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.figure_context import collect_document_figures
from latex_linting.rules.model import Rule
from latex_linting.rules.table_context import collect_document_tables
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_PLACEMENT_RE = re.compile(r"\[([^\]\r\n]+)\]")


def _find_optional_bracket(source: Source, begin_token: Token) -> tuple[int, str] | None:
    """Return start offset and content of optional bracket argument following begin_token if present."""
    text = source.text
    idx = begin_token.end
    text_len = len(text)
    while idx < text_len:
        if text[idx].isspace():
            idx += 1
        elif text[idx] == "%":
            nl_pos = text.find("\n", idx)
            idx = text_len if nl_pos == -1 else nl_pos + 1
        else:
            break
    if idx < text_len and text[idx] == "[":
        match = _PLACEMENT_RE.match(text, idx)
        if match:
            return idx, match.group(0)
    return None


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Warn when optional placement parameters are used on figure or table floats."""
    fig_floats, _, _ = collect_document_figures(document)
    tab_floats, _ = collect_document_tables(document)

    all_floats = [(f.source, f.begin_token, f.env_name) for f in fig_floats] + [
        (t.source, t.begin_token, t.env_name) for t in tab_floats
    ]

    for source, begin_token, env_name in all_floats:
        bracket_info = _find_optional_bracket(source, begin_token)
        if bracket_info is not None:
            start_offset, bracket_str = bracket_info
            explanation = (
                f"Do not use optional placement argument '{bracket_str}' on '{env_name}'; "
                "let the template defaults control float positioning."
            )
            correction = f"Remove '{bracket_str}' to use default float placement."
            yield source.finding(start_offset, RULE.rule_id, explanation, correction, severity=RULE.severity)


RULE = Rule(
    rule_id="FLOAT-01",
    explanation="Float environments should not use optional placement arguments. Usually the document class defaults are prefered",
    correction="Remove optional placement arguments from figure and table environments or add ignore comment.",
    passing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{A properly floating figure.}\\label{fig:plot}\n"
            "\\end{figure}\n"
            "See Figure~\\ref{fig:plot}."
        ),
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\caption{A properly floating table.}\\label{tab:data}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    A & B \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}\n"
            "See Table~\\ref{tab:data}."
        ),
    ),
    failing_examples=(
        (
            "\\begin{figure}[!tb]\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{A figure with manual placement.}\\label{fig:plot}\n"
            "\\end{figure}\n"
            "See Figure~\\ref{fig:plot}."
        ),
        (
            "\\begin{table}[htbp]\n"
            "  \\centering\n"
            "  \\caption{A table with manual placement.}\\label{tab:data}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    A & B \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}\n"
            "See Table~\\ref{tab:data}."
        ),
    ),
    limits=(
        "Detects optional placement arguments in square brackets immediately following "
        "\\begin{figure}, \\begin{figure*}, \\begin{table}, and \\begin{table*}. "
        "Whitespace and comments between the environment name and the bracket argument are ignored. "
        "Reports the opening bracket position as a warning."
    ),
    evaluate=_evaluate,
    enabled_by_default=True,
    severity="warning",
)
