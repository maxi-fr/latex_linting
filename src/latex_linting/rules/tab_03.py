from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.table_context import collect_document_tables
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check centering in table floats and reject the center environment inside floats."""
    all_floats, _ = collect_document_tables(document)

    for table_float in all_floats:
        for center_token in table_float.center_env_tokens:
            explanation = (
                "Do not use the 'center' environment inside a table float; "
                "use '\\centering' instead to avoid unwanted vertical whitespace."
            )
            correction = "Replace '\\begin{center}...\\end{center}' with '\\centering'."
            yield table_float.source.finding(center_token.start, RULE.rule_id, explanation, correction)

        if not table_float.has_centering and not table_float.center_env_tokens:
            explanation = "Table float is missing a '\\centering' declaration."
            correction = "Add '\\centering' inside the table environment."
            yield table_float.source.finding(table_float.begin_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="TAB-03",
    explanation="Table floats must be centered with '\\centering' rather than the 'center' environment.",
    correction="Use '\\centering' inside the table environment and remove 'center' environments.",
    passing_examples=(
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\caption{Properly centered table.}\n"
            "  \\label{tab:centered}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Key & Value \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}"
        ),
        (
            "\\begin{table*}\n"
            "  \\centering\n"
            "  \\caption{Wide table with centering.}\n"
            "  \\label{tab:wide}\n"
            "  \\begin{tabular}{lll}\n"
            "    \\toprule\n"
            "    A & B & C \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table*}"
        ),
    ),
    failing_examples=(
        (
            "\\begin{table}\n"
            "  \\begin{center}\n"
            "    \\caption{Table using center environment.}\n"
            "    \\label{tab:center_env}\n"
            "    \\begin{tabular}{ll}\n"
            "      \\toprule\n"
            "      Key & Value \\\\\n"
            "      \\bottomrule\n"
            "    \\end{tabular}\n"
            "  \\end{center}\n"
            "\\end{table}"
        ),
        (
            "\\begin{table}\n"
            "  \\caption{Table lacking centering declaration.}\n"
            "  \\label{tab:no_centering}\n"
            "  \\begin{tabular}{ll}\n"
            "    \\toprule\n"
            "    Key & Value \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabular}\n"
            "\\end{table}"
        ),
    ),
    limits=(
        "Checks for centering inside table and table* float environments. Rejects the 'center' "
        "environment (\\begin{center}...\\end{center}) because it introduces unwanted vertical whitespace, "
        "recommending '\\centering' instead. Flags table floats lacking a '\\centering' declaration. "
        "Findings attach to '\\begin{center}' when the center environment is used, or to '\\begin{table}' "
        "(or '\\begin{table*}') when centering is missing. Does not inspect figure environments (governed "
        "by FIG-08) or standalone tabulars outside float environments."
    ),
    evaluate=_evaluate,
)
