from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.table_context import collect_document_tables
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check that table caption precedes tabular content and label follows caption."""
    all_floats, _ = collect_document_tables(document)

    for table_float in all_floats:
        first_caption = table_float.captions[0] if table_float.captions else None

        for caption in table_float.captions:
            if any(tabular.start < caption.command_token.start for tabular in table_float.tabular_tokens):
                explanation = "Table caption must be placed above the tabular content."
                correction = "Move '\\caption{...}' above the tabular environment."
                yield table_float.source.finding(caption.command_token.start, RULE.rule_id, explanation, correction)

        for lbl in table_float.labels:
            if not lbl.is_inside_caption and (
                first_caption is None or lbl.command_token.start < first_caption.command_token.start
            ):
                explanation = "Table label must be placed inside or after '\\caption'."
                correction = "Move '\\label{...}' inside or immediately following '\\caption'."
                yield table_float.source.finding(lbl.command_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="TAB-02",
    explanation=(
        "In a table float, the caption must precede the tabular content and the label must "
        "follow or be inside the caption."
    ),
    correction=(
        "Place '\\caption{...}' above the tabular environment, and place '\\label{tab:...}' "
        "inside or following '\\caption'."
    ),
    passing_examples=(
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\caption{Measured performance results.}\n"
            "  \\label{tab:perf}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Trial & Result \\\\\n"
            "    \\midrule\n"
            "    1 & 42 \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}"
        ),
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\caption{Measured performance results.\\label{tab:perf}}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Trial & Result \\\\\n"
            "    \\midrule\n"
            "    1 & 42 \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}"
        ),
    ),
    failing_examples=(
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Trial & Result \\\\\n"
            "    \\midrule\n"
            "    1 & 42 \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "  \\caption{Caption placed below table.}\n"
            "  \\label{tab:wrong_order}\n"
            "\\end{table}"
        ),
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\label{tab:early_label}\n"
            "  \\caption{Caption placed after label.}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Trial & Result \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}"
        ),
    ),
    limits=(
        "Checks that '\\caption{...}' appears before tabular environments (tabular, tabular*, "
        "tabularx, tabulary, longtable) inside table and table* float environments, and that "
        "'\\label{...}' is enclosed within or placed after '\\caption{...}'. Flags captions "
        "placed below tabular content at '\\caption', and labels placed before captions at "
        "'\\label'. Labels enclosed directly in '\\caption{...\\label{...}}' are supported and "
        "valid. Does not check standalone tabulars outside float environments or evaluate caption "
        "prose quality."
    ),
    evaluate=_evaluate,
)
