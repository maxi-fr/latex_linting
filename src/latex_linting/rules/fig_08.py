from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.figure_context import collect_document_figures
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check centering in figure floats and reject the center environment inside floats."""
    all_floats, _, _ = collect_document_figures(document)

    for fig_float in all_floats:
        for center_token in fig_float.center_env_tokens:
            explanation = (
                "Do not use the 'center' environment inside a figure float; "
                "use '\\centering' instead to avoid unwanted vertical whitespace."
            )
            correction = "Replace '\\begin{center}...\\end{center}' with '\\centering'."
            yield fig_float.source.finding(center_token.start, RULE.rule_id, explanation, correction)

        if not fig_float.has_centering and not fig_float.center_env_tokens:
            explanation = "Figure float is missing a '\\centering' declaration."
            correction = "Add '\\centering' inside the figure environment."
            yield fig_float.source.finding(fig_float.begin_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="FIG-08",
    explanation="Figures must be centered with '\\centering' rather than the 'center' environment.",
    correction="Use '\\centering' inside the figure environment and remove 'center' environments.",
    passing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{A properly centered plot.}\n"
            "  \\label{fig:plot}\n"
            "\\end{figure}\n"
            "As seen in Figure~\\ref{fig:plot}, the data align."
        ),
        (
            "\\begin{figure*}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/wide.pdf}\n"
            "  \\caption{Wide plot with centering.}\n"
            "  \\label{fig:wide}\n"
            "\\end{figure*}\n"
            "See~\\autoref{fig:wide} for details."
        ),
    ),
    failing_examples=(
        (
            "\\begin{figure}\n"
            "  \\begin{center}\n"
            "    \\includegraphics{figures/plot.pdf}\n"
            "  \\end{center}\n"
            "  \\caption{Plot with center environment.}\n"
            "  \\label{fig:plot}\n"
            "\\end{figure}"
        ),
        (
            "\\begin{figure}\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Plot lacking centering.}\n"
            "  \\label{fig:plot}\n"
            "\\end{figure}"
        ),
    ),
    limits=(
        "Checks for centering inside figure and figure* float environments. Rejects the center "
        "environment (\\begin{center}...\\end{center}) because it adds unwanted vertical whitespace. "
        "Flags figure floats lacking a \\centering declaration. Findings attach to \\begin{center} "
        "when the center environment is used, or to \\begin{figure} when \\centering is missing. "
        "Does not inspect table environments, which are governed by TAB-03."
    ),
    evaluate=_evaluate,
)
