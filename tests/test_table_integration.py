from pathlib import Path

from latex_linting.main import check


def test_multi_finding_table_all_violations(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\begin{center}\n"
        "    \\begin{tabular}{|l|r|}\n"
        "      \\hline\n"
        "      A & B \\\\\n"
        "      \\cline{1-2}\n"
        "      1 & 2 \\\\\n"
        "    \\end{tabular}\n"
        "    \\caption{Misplaced caption.}\n"
        "    \\label{tab:multi}\n"
        "  \\end{center}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TAB-01" in rule_ids
    assert "TAB-02" in rule_ids
    assert "TAB-03" in rule_ids


def test_multi_finding_table_targeted_suppression_leaves_others_visible(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    # Same table, but TAB-01 is ignored on the tabular line
    root.write_text(
        "\\begin{table}\n"
        "  \\begin{center}\n"
        "    \\begin{tabular}{|l|r|} % latex-lint:ignore=TAB-01\n"
        "      \\toprule\n"
        "      A & B \\\\\n"
        "      \\bottomrule\n"
        "    \\end{tabular}\n"
        "    \\caption{Misplaced caption.}\n"
        "    \\label{tab:multi}\n"
        "  \\end{center}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TAB-01" not in rule_ids
    assert "TAB-02" in rule_ids
    assert "TAB-03" in rule_ids


def test_multi_finding_table_targeted_suppression_of_tab_02(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\begin{center}\n"
        "    \\begin{tabular}{|l|r|}\n"
        "      \\toprule\n"
        "      A & B \\\\\n"
        "      \\bottomrule\n"
        "    \\end{tabular}\n"
        "    \\caption{Misplaced caption.} % latex-lint:ignore=TAB-02\n"
        "    \\label{tab:multi}\n"
        "  \\end{center}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TAB-01" in rule_ids
    assert "TAB-02" not in rule_ids
    assert "TAB-03" in rule_ids


def test_multi_finding_table_targeted_suppression_of_tab_03(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\begin{center} % latex-lint:ignore=TAB-03\n"
        "    \\caption{Early caption.}\n"
        "    \\label{tab:multi}\n"
        "    \\begin{tabular}{|l|r|}\n"
        "      \\toprule\n"
        "      A & B \\\\\n"
        "      \\bottomrule\n"
        "    \\end{tabular}\n"
        "  \\end{center}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TAB-01" in rule_ids
    assert "TAB-02" not in rule_ids
    assert "TAB-03" not in rule_ids


def test_valid_booktabs_table_float(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}[htbp]\n"
        "  \\centering\n"
        "  \\caption{Completely valid table float.}\n"
        "  \\label{tab:valid}\n"
        "  \\begin{tabular}{llr}\n"
        "    \\toprule\n"
        "    Item & Category & Count \\\\\n"
        "    \\midrule\n"
        "    Alpha & Primary & 10 \\\\\n"
        "    Beta & Secondary & 20 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id in ("TAB-01", "TAB-02", "TAB-03")]
    assert findings == []
