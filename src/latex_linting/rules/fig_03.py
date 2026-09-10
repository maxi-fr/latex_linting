from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.figure_context import (
    collect_document_figures,
    collect_document_references,
)
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate figure float environments, required labels, duplicates, and document-wide references."""
    referenced = collect_document_references(document)
    all_floats, outside_images, label_counts = collect_document_figures(document)

    for source, token in outside_images:
        explanation = "Figure content must be enclosed in a 'figure' or 'figure*' float environment."
        correction = "Wrap this figure content in a '\\begin{figure}...\\end{figure}' environment."
        yield source.finding(token.start, RULE.rule_id, explanation, correction)

    for fig_float in all_floats:
        if not fig_float.labels:
            explanation = "Figure float is missing a '\\label' command."
            correction = "Add a '\\label{fig:...}' command inside or after the caption."
            yield fig_float.source.finding(fig_float.begin_token.start, RULE.rule_id, explanation, correction)
            continue

        for lbl in fig_float.labels:
            if label_counts[lbl.target] > 1:
                explanation = f"Duplicate figure label '{lbl.target}'."
                correction = "Use a unique label for this figure."
                yield fig_float.source.finding(lbl.command_token.start, RULE.rule_id, explanation, correction)
            elif lbl.target not in referenced:
                explanation = f"Figure label '{lbl.target}' is never referenced in the document."
                correction = (
                    f"Reference this figure using \\ref{{{lbl.target}}}, "
                    f"\\autoref{{{lbl.target}}}, \\cref{{{lbl.target}}}, or \\Cref{{{lbl.target}}}."
                )
                yield fig_float.source.finding(lbl.command_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="FIG-03",
    explanation="Figures must float in a figure environment, declare a unique label, and be referenced in text.",
    correction="Wrap figure content in 'figure', add a unique '\\label{fig:...}', and reference it with \\ref{...}.",
    passing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/model.pdf}\n"
            "  \\caption{System architecture diagram.}\n"
            "  \\label{fig:model}\n"
            "\\end{figure}\n"
            "As seen in Figure~\\ref{fig:model}, the pipeline processes input data."
        ),
        (
            "\\begin{figure*}\n"
            "  \\centering\n"
            "  \\begin{tikzpicture}\n"
            "    \\draw (0,0) -- (1,1);\n"
            "  \\end{tikzpicture}\n"
            "  \\caption{Overview diagram.\\label{fig:overview}}\n"
            "\\end{figure*}\n"
            "See~\\autoref{fig:overview} for details."
        ),
    ),
    failing_examples=(
        "\\includegraphics{figures/logo.pdf}",
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Unlabeled plot.}\n"
            "\\end{figure}"
        ),
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Unreferenced plot.}\n"
            "  \\label{fig:unused}\n"
            "\\end{figure}"
        ),
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/a.pdf}\n"
            "  \\caption{First figure.}\n"
            "  \\label{fig:dup}\n"
            "\\end{figure}\n"
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/b.pdf}\n"
            "  \\caption{Second figure.}\n"
            "  \\label{fig:dup}\n"
            "\\end{figure}"
        ),
    ),
    limits=(
        "Detects figure content (\\includegraphics, \\begin{tikzpicture}) outside figure or figure* "
        "float environments, figure floats missing a \\label declaration, duplicate figure labels "
        "across the entire document, and figure labels never referenced by recognized commands "
        "(\\ref, \\autoref, \\cref, \\Cref). References collected from other included sources "
        "satisfy the check. References in comments or literal code (verbatim, listings) do not count. "
        "Actionable locations attach to \\includegraphics or \\begin{tikzpicture} when outside floats, "
        "to \\begin{figure} when missing labels, or to \\label for duplicate or unreferenced labels. "
        "Does not check file existence on disk, render output, or evaluate plot appearance."
    ),
    evaluate=_evaluate,
)
