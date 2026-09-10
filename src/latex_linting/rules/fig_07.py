from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.figure_context import collect_document_figures
from latex_linting.rules.model import Rule
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check standard ordering inside figure floats: image content, then caption, then label."""
    all_floats, _, _ = collect_document_figures(document)

    for fig_float in all_floats:
        first_caption = fig_float.captions[0] if fig_float.captions else None

        for caption in fig_float.captions:
            if any(img.start > caption.command_token.start for img in fig_float.image_tokens):
                explanation = "Caption must be placed below the figure image content."
                correction = "Move '\\caption{...}' below the image content."
                yield fig_float.source.finding(caption.command_token.start, RULE.rule_id, explanation, correction)

        if first_caption is not None:
            for lbl in fig_float.labels:
                if not lbl.is_inside_caption and lbl.command_token.start < first_caption.command_token.start:
                    explanation = "Figure label must be placed inside or after '\\caption'."
                    correction = "Move '\\label{...}' inside or immediately following '\\caption'."
                    yield fig_float.source.finding(lbl.command_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="FIG-07",
    explanation="Inside a figure float, image content must precede caption, and caption must precede or enclose label.",
    correction="Place image content first, followed by '\\caption{...}', followed by '\\label{fig:...}'.",
    passing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{A plot of measured frequencies.}\n"
            "  \\label{fig:freq}\n"
            "\\end{figure}\n"
            "As seen in Figure~\\ref{fig:freq}, the frequencies match."
        ),
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\begin{tikzpicture}\n"
            "    \\draw (0,0) -- (1,1);\n"
            "  \\end{tikzpicture}\n"
            "  \\caption{A TikZ diagram.\\label{fig:diagram}}\n"
            "\\end{figure}\n"
            "See \\autoref{fig:diagram} for details."
        ),
    ),
    failing_examples=(
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\caption{Caption placed before image.}\n"
            "  \\label{fig:wrong_order}\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "\\end{figure}"
        ),
        (
            "\\begin{figure}\n"
            "  \\centering\n"
            "  \\label{fig:early_label}\n"
            "  \\includegraphics{figures/plot.pdf}\n"
            "  \\caption{Caption placed after label.}\n"
            "\\end{figure}"
        ),
    ),
    limits=(
        "Checks the standard ordering of figure components inside figure and figure* environments: "
        "image content (\\includegraphics, \\begin{tikzpicture}, \\input), followed by \\caption, "
        "followed or enclosed by \\label. Flags captions placed above any image content, and flags "
        "labels placed before \\caption. Labels enclosed directly within \\caption{...\\label{...}} "
        "are supported and valid. Findings attach to \\caption when preceding images, or to \\label "
        "when preceding captions."
    ),
    evaluate=_evaluate,
)
