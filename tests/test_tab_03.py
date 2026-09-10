from pathlib import Path

from latex_linting.main import check


def test_valid_table_with_centering(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\caption{Properly centered table.}\n"
        "  \\label{tab:centered}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    Key & Value \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert findings == []


def test_valid_table_star_with_centering(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table*}\n"
        "  \\centering\n"
        "  \\caption{Wide table with centering.}\n"
        "  \\label{tab:wide}\n"
        "  \\begin{tabular}{lll}\n"
        "    \\toprule\n"
        "    A & B & C \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert findings == []


def test_flags_missing_centering_in_table(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\caption{Table lacking centering.}\n"
        "  \\label{tab:nocenter}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1
    assert "missing a '\\centering' declaration" in findings[0].explanation


def test_flags_missing_centering_in_table_star(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table*}\n"
        "  \\caption{Wide table lacking centering.}\n"
        "  \\label{tab:nocenter_star}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1


def test_flags_center_environment_in_table(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\begin{center}\n"
        "    \\caption{Table with center environment.}\n"
        "    \\label{tab:center_env}\n"
        "    \\begin{tabular}{ll}\n"
        "      \\toprule\n"
        "      1 & 2 \\\\\n"
        "      \\bottomrule\n"
        "    \\end{tabular}\n"
        "  \\end{center}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 3
    assert "Do not use the 'center' environment" in findings[0].explanation


def test_flags_center_environment_in_table_star(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table*}\n"
        "  \\begin{center}\n"
        "    \\caption{Wide table with center environment.}\n"
        "    \\label{tab:center_star}\n"
        "    \\begin{tabular}{ll}\n"
        "      1 & 2 \\\\\n"
        "    \\end{tabular}\n"
        "  \\end{center}\n"
        "\\end{table*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 3


def test_does_not_flag_center_environment_outside_table(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{center}\n  Some centered text outside any float.\n\\end{center}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert findings == []


def test_table_with_placement_arguments(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}[htbp]\n"
        "  \\centering\n"
        "  \\caption{Table with placement options.}\n"
        "  \\label{tab:place}\n"
        "  \\begin{tabular}{ll}\n"
        "    1 & 2 \\\\\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert findings == []


def test_tab_03_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table} % latex-lint:ignore=TAB-03\n"
        "  \\caption{Suppressed missing centering.}\n"
        "  \\label{tab:suppressed}\n"
        "  \\begin{tabular}{ll}\n"
        "    1 & 2 \\\\\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert findings == []


def test_tab_03_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=TAB-03\n"
        "\\begin{table}\n"
        "  \\caption{Disabled table.}\n"
        "  \\begin{tabular}{ll} 1 & 2 \\end{tabular}\n"
        "\\end{table}\n"
        "% latex-lint:enable=TAB-03\n"
        "\\begin{table}\n"
        "  \\caption{Enabled table.}\n"
        "  \\begin{tabular}{ll} 1 & 2 \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-03"]
    assert len(findings) == 1
    assert findings[0].line == 7
