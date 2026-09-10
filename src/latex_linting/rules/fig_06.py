from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.figure_context import collect_document_figures
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check that figure floats contain a caption and that captions end with a full stop."""
    all_floats, _, _ = collect_document_figures(document)

    for fig_float in all_floats:
        if not fig_float.captions:
            explanation = "Figure float is missing a '\\caption' command."
            correction = "Add a '\\caption{...}' command describing the figure."
            yield fig_float.source.finding(fig_float.begin_token.start, RULE.rule_id, explanation, correction)
            continue

        for caption in fig_float.captions:
            if not caption.text.rstrip().endswith("."):
                explanation = "Figure caption must end with a full stop."
                correction = "Add a terminal full stop '.' at the end of the caption text."
                yield fig_float.source.finding(caption.command_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="FIG-06",
    explanation="Every figure float must carry a caption ending with a full stop.",
    correction="Add a '\\caption{...}' command ending with a terminal full stop '.'.",
    passing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/model.pdf}\n"
            "  \\caption{System architecture diagram showing module interactions.}\n"
            "  \\label{fig:model}\n"
            "\\end{figure}\n"
            "As seen in Figure~\\ref{fig:model}, the pipeline processes input data."
        ),
        (
            "\\begin{figure*}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/wide.pdf}\n"
            "  \\caption[Overview]{Comprehensive view of experimental outcomes.\\label{fig:wide}}\n"
            "\\end{figure*}\n"
            "See~\\autoref{fig:wide} for details."
        ),
    ),
    failing_examples=(
        ("\\begin{figure}\n  \\centering\n  \\includegraphics{figures/plot.pdf}\n  \\label{fig:plot}\n\\end{figure}"),
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Measured output signals without full stop}\n"
            "  \\label{fig:plot}\n"
            "\\end{figure}"
        ),
    ),
    limits=(
        "Checks that every figure and figure* float environment contains a \\caption command and that "
        "the caption text ends with a terminal full stop ('.'). Handles optional short captions "
        "(\\caption[short]{full text.}), multiline captions, nested inline math, and nested \\label "
        "commands. Attach locations point to \\begin{figure} when a caption is missing, or to \\caption "
        "when a terminal full stop is missing. Does not judge whether the caption is comprehensive, "
        "understandable, or grammatically complete."
    ),
    evaluate=_evaluate,
)
