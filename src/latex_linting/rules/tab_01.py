from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.table_context import collect_document_tables
from latex_linting.source import Finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Check booktabs conventions: reject vertical rules in column specs and forbid hline/cline."""
    all_floats, all_tabulars = collect_document_tables(document)

    for tabular in all_tabulars:
        for pipe_offset in tabular.pipe_offsets:
            explanation = (
                "Do not use vertical rules ('|') in table column specifications; "
                "booktabs tables use only horizontal rules."
            )
            correction = "Remove '|' from the column specification."
            yield tabular.source.finding(pipe_offset, RULE.rule_id, explanation, correction)

        for rule_token in tabular.forbidden_rules:
            if rule_token.value == r"\hline":
                explanation = (
                    "Do not use '\\hline'; booktabs tables use '\\toprule', '\\midrule', "
                    "and '\\bottomrule' for horizontal rules."
                )
                correction = "Replace '\\hline' with '\\toprule', '\\midrule', or '\\bottomrule'."
            else:
                explanation = "Do not use '\\cline'; booktabs tables use '\\cmidrule' for partial horizontal rules."
                correction = "Replace '\\cline' with '\\cmidrule'."
            yield tabular.source.finding(rule_token.start, RULE.rule_id, explanation, correction)

    for table_float in all_floats:
        for rule_token in table_float.forbidden_rules:
            if rule_token.value == r"\hline":
                explanation = (
                    "Do not use '\\hline'; booktabs tables use '\\toprule', '\\midrule', "
                    "and '\\bottomrule' for horizontal rules."
                )
                correction = "Replace '\\hline' with '\\toprule', '\\midrule', or '\\bottomrule'."
            else:
                explanation = "Do not use '\\cline'; booktabs tables use '\\cmidrule' for partial horizontal rules."
                correction = "Replace '\\cline' with '\\cmidrule'."
            yield table_float.source.finding(rule_token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="TAB-01",
    explanation=(
        "Tables must follow booktabs conventions: avoid vertical rules ('|') in column specifications "
        "and replace '\\hline' and '\\cline' with booktabs horizontal rule commands."
    ),
    correction=(
        "Remove vertical rules ('|') from column specifications and use '\\toprule', '\\midrule', "
        "'\\bottomrule', or '\\cmidrule' instead of '\\hline' or '\\cline'."
    ),
    passing_examples=(
        (
            "\\begin{tabular}{llr}\n"
            "  \\toprule\n"
            "  Name & Category & Score \\\\\n"
            "  \\midrule\n"
            "  Alpha & First & 95 \\\\\n"
            "  Beta & Second & 88 \\\\\n"
            "  \\bottomrule\n"
            "\\end{tabular}"
        ),
        (
            "\\begin{table}\n"
            "  \\centering\n"
            "  \\caption{Summary of experimental metrics.}\n"
            "  \\label{tab:metrics}\n"
            "  \\begin{tabularx}{\\textwidth}{X r r}\n"
            "    \\toprule\n"
            "    Metric & Baseline & Proposed \\\\\n"
            "    \\midrule\n"
            "    Accuracy & 0.82 & 0.94 \\\\\n"
            "    \\bottomrule\n"
            "  \\end{tabularx}\n"
            "\\end{table}"
        ),
    ),
    failing_examples=(
        (
            "\\begin{tabular}{|l|c|r|}\n"
            "  \\hline\n"
            "  Name & Category & Score \\\\\n"
            "  \\hline\n"
            "  Alpha & First & 95 \\\\\n"
            "  \\hline\n"
            "\\end{tabular}"
        ),
        (
            "\\begin{tabular}{l c r}\n"
            "  \\hline\n"
            "  Item & Count & Value \\\\\n"
            "  \\cline{2-3}\n"
            "  A & 1 & 10 \\\\\n"
            "  \\hline\n"
            "\\end{tabular}"
        ),
    ),
    limits=(
        "Detects vertical rules ('|') in column specifications of supported tabular environments "
        "(tabular, tabular*, tabularx, tabulary, longtable), including nested repetition constructs "
        "(*{...}{...}) and optional placement arguments. Rejects '\\hline' and '\\cline' horizontal "
        "rule commands inside tabular environments in favor of booktabs commands (\\toprule, \\midrule, "
        "\\bottomrule, \\cmidrule). Does not flag vertical bars in math mode ($|x|$), text mode, code blocks, "
        "or comments outside column specifications. Does not inspect semantic column contents, units, "
        "or rendered table layout."
    ),
    evaluate=_evaluate,
)
