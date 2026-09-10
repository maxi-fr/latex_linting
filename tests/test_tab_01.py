from pathlib import Path

from latex_linting.main import check


def test_valid_booktabs_table(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{llr}\n"
        "  \\toprule\n"
        "  Name & Category & Score \\\\\n"
        "  \\midrule\n"
        "  Alpha & First & 95 \\\\\n"
        "  Beta & Second & 88 \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_valid_tabularx_and_cmidrule(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabularx}{\\textwidth}{X r r}\n"
        "  \\toprule\n"
        "  Metric & Trial 1 & Trial 2 \\\\\n"
        "  \\cmidrule(r){1-1} \\cmidrule(l){2-3}\n"
        "  Accuracy & 0.85 & 0.92 \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabularx}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_valid_longtable_booktabs(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{longtable}[c]{l c r}\n"
        "  \\toprule\n"
        "  A & B & C \\\\\n"
        "  \\midrule\n"
        "  1 & 2 & 3 \\\\\n"
        "  \\bottomrule\n"
        "\\end{longtable}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_valid_repetition_construct_no_vertical_bars(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{*{3}{c}}\n  \\toprule\n  1 & 2 & 3 \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_valid_nested_column_arguments(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{p{3cm} >{\\bfseries}l @{\\extracolsep{\\fill}} r}\n"
        "  \\toprule\n"
        "  Header & Value & Note \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_critical_does_not_flag_math_vertical_bar(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{ll}\n"
        "  \\toprule\n"
        "  $|x| < 1$ & $\\|v\\| = 1$ \\\\\n"
        "  $P(A|B)$ & $\\{x \\mid x > 0\\}$ \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_critical_does_not_flag_text_pipe_in_cells(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{ll}\n  \\toprule\n  A | B & C | D \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_critical_does_not_flag_literal_code_pipe(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{ll}\n"
        "  \\toprule\n"
        "  \\verb|cat file | grep x| & Output \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_critical_does_not_flag_pipe_in_comments(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{\n"
        "  l % note: do not use | here\n"
        "  r\n"
        "}\n"
        "  \\toprule\n"
        "  % row comment with |\n"
        "  1 & 2 \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_critical_does_not_flag_pipe_outside_tables(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "In Unix commands, the | symbol is called a pipe. Also $|x| \\ge 0$.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert findings == []


def test_flags_vertical_rules_in_tabular_cols(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{|l|c|r|}\n  \\toprule\n  A & B & C \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 4
    assert findings[0].line == 1
    assert findings[0].column == 17
    assert findings[1].column == 19
    assert findings[2].column == 21
    assert findings[3].column == 23
    assert "vertical rules" in findings[0].explanation


def test_flags_double_vertical_rules(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{l||r}\n  \\toprule\n  1 & 2 \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2
    assert findings[0].column == 18
    assert findings[1].column == 19


def test_flags_vertical_rules_in_repetition_construct(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{*{3}{|c}}\n  \\toprule\n  1 & 2 & 3 \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 1
    assert findings[0].column == 22


def test_flags_vertical_rules_in_nested_repetition(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{*{2}{*{3}{|c}}}\n  \\toprule\n  1 & 2 & 3 \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 1
    assert findings[0].column == 27


def test_flags_vertical_rules_with_optional_arguments(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}[t]{|l c|}\n  \\toprule\n  1 & 2 \\\\\n  \\bottomrule\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2
    assert findings[0].column == 20
    assert findings[1].column == 24


def test_flags_vertical_rules_in_tabular_star(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular*}{\\linewidth}[t]{|l c|}\n  \\toprule\n  1 & 2 \\\\\n  \\bottomrule\n\\end{tabular*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2
    assert findings[0].column == 33
    assert findings[1].column == 37


def test_flags_vertical_rules_in_tabularx(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabularx}{\\linewidth}[b]{|X X|}\n  \\toprule\n  A & B \\\\\n  \\bottomrule\n\\end{tabularx}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2
    assert findings[0].column == 33
    assert findings[1].column == 37


def test_flags_vertical_rules_in_tabulary(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabulary}{\\textwidth}{|L C|}\n  \\toprule\n  A & B \\\\\n  \\bottomrule\n\\end{tabulary}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2


def test_flags_vertical_rules_in_longtable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{longtable}[c]{|l|r|}\n  \\toprule\n  1 & 2 \\\\\n  \\bottomrule\n\\end{longtable}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 3


def test_flags_hline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{ll}\n  \\hline\n  A & B \\\\\n  \\hline\n  1 & 2 \\\\\n  \\hline\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 3
    assert findings[0].line == 2
    assert findings[0].column == 3
    assert "\\toprule" in findings[0].correction


def test_flags_cline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{llr}\n"
        "  \\toprule\n"
        "  A & B & C \\\\\n"
        "  \\cline{1-2}\n"
        "  1 & 2 & 3 \\\\\n"
        "  \\bottomrule\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert findings[0].column == 3
    assert "\\cmidrule" in findings[0].correction


def test_flags_hline_in_longtable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{longtable}{ll}\n  \\hline\n  1 & 2 \\\\\n  \\hline\n\\end{longtable}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2


def test_multiline_column_spec_exact_positions(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{\n  |l\n  |c\n  |r|\n}\n  1 & 2 & 3 \\\\\n\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    # 4 pipe findings on lines 2, 3, 4, 4 plus 0 hlines
    assert len(findings) == 4
    assert findings[0].line == 2
    assert findings[0].column == 3
    assert findings[1].line == 3
    assert findings[1].column == 3
    assert findings[2].line == 4
    assert findings[2].column == 3
    assert findings[3].line == 4
    assert findings[3].column == 5


def test_tab_01_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tabular}{\n"
        "  |l\n"
        "  |c % latex-lint:ignore=TAB-01\n"
        "  |r\n"
        "}\n"
        "  \\hline % latex-lint:ignore=TAB-01\n"
        "  1 & 2 & 3 \\\\\n"
        "  \\hline\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    # Line 3 (|c) and Line 6 (\hline) suppressed; line 2 (|l), line 4 (|r), and line 8 (\hline) remain
    lines = [f.line for f in findings]
    assert 3 not in lines
    assert 6 not in lines
    assert 2 in lines
    assert 4 in lines
    assert 8 in lines


def test_tab_01_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=TAB-01\n"
        "\\begin{tabular}{|l|r|}\n"
        "  \\hline\n"
        "  1 & 2 \\\\\n"
        "\\end{tabular}\n"
        "% latex-lint:enable=TAB-01\n"
        "\\begin{tabular}{|c|}\n"
        "  1 \\\\\n"
        "\\end{tabular}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TAB-01"]
    assert len(findings) == 2
    assert all(f.line >= 7 for f in findings)
