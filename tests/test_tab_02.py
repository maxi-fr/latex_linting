from pathlib import Path

from latex_linting.main import check


def test_valid_caption_precedes_tabular_label_follows(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
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
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_valid_label_inside_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\caption{Measured performance results.\\label{tab:perf}}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    Trial & Result \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_valid_table_star_environment(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table*}\n"
        "  \\centering\n"
        "  \\caption{Full width table.}\n"
        "  \\label{tab:full}\n"
        "  \\begin{tabular}{lll}\n"
        "    \\toprule\n"
        "    A & B & C \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_valid_caption_with_optional_short_title(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\caption[Short title]{Full detailed table title.}\n"
        "  \\label{tab:short}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_valid_caption_with_nested_formatting(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\caption{Results for \\textbf{Method} and $\\alpha$ parameter.}\n"
        "  \\label{tab:nested}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_flags_caption_placed_after_tabular(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "  \\caption{Caption placed below table.}\n"
        "  \\label{tab:below}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 1
    assert findings[0].line == 8
    assert findings[0].column == 3
    assert "above the tabular content" in findings[0].explanation


def test_flags_label_placed_before_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\label{tab:early}\n"
        "  \\caption{Caption placed after label.}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 1
    assert findings[0].line == 3
    assert findings[0].column == 3
    assert "inside or after" in findings[0].explanation


def test_flags_both_when_caption_after_tabular_and_label_before_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "  \\label{tab:misplaced}\n"
        "  \\caption{Caption misplaced too.}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 2
    # One on caption (line 9), one on label (line 8)
    assert any(f.line == 9 for f in findings)
    assert any(f.line == 8 for f in findings)


def test_flags_label_when_no_caption_in_table_float(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\label{tab:nocaption}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 1
    assert findings[0].line == 3


def test_caption_and_label_order_with_multiple_tabulars(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "  \\caption{Misplaced caption between tables.}\n"
        "  \\label{tab:mid}\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    3 & 4 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 1
    assert findings[0].line == 8


def test_tab_02_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll}\n"
        "    \\toprule\n"
        "    1 & 2 \\\\\n"
        "    \\bottomrule\n"
        "  \\end{tabular}\n"
        "  \\caption{Caption suppressed.} % latex-lint:ignore=TAB-02\n"
        "  \\label{tab:suppressed}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert findings == []


def test_tab_02_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=TAB-02\n"
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll} 1 & 2 \\end{tabular}\n"
        "  \\caption{Disabled table.}\n"
        "  \\label{tab:disabled}\n"
        "\\end{table}\n"
        "% latex-lint:enable=TAB-02\n"
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\begin{tabular}{ll} 1 & 2 \\end{tabular}\n"
        "  \\caption{Enabled table.}\n"
        "  \\label{tab:enabled}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-02"]
    assert len(findings) == 1
    assert findings[0].line == 12
