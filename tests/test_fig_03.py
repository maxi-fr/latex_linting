from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_figure_with_label_and_reference(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/model.pdf}\n"
        "  \\caption{System architecture diagram.}\n"
        "  \\label{fig:model}\n"
        "\\end{figure}\n"
        "As seen in Figure~\\ref{fig:model}, the system operates in stages.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


@pytest.mark.parametrize("ref_cmd", [r"\ref", r"\autoref", r"\cref", r"\Cref"])
def test_valid_figure_with_various_reference_commands(tmp_path: Path, ref_cmd: str) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/flow.pdf}\n"
        "  \\caption{Process flow.}\n"
        "  \\label{fig:flow}\n"
        "\\end{figure}\n"
        f"See {ref_cmd}{{fig:flow}} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_valid_figure_with_label_inside_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Measured output signals.\\label{fig:signals}}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:signals} displays the results.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_valid_starred_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}[t]\n"
        "  \\centering\n"
        "  \\includegraphics{figures/wide.pdf}\n"
        "  \\caption{Wide two-column layout overview.}\n"
        "  \\label{fig:wide}\n"
        "\\end{figure*}\n"
        "See \\ref{fig:wide} for the comprehensive view.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_valid_tikzpicture_in_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\begin{tikzpicture}\n"
        "    \\draw (0,0) -- (1,1);\n"
        "  \\end{tikzpicture}\n"
        "  \\caption{A simple line drawing.}\n"
        "  \\label{fig:drawing}\n"
        "\\end{figure}\n"
        "The line in Figure~\\ref{fig:drawing} illustrates continuity.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_violating_includegraphic_outside_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Here is an inline logo:\n\\includegraphics{figures/logo.pdf}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 1
    assert "\\includegraphics{figures/logo.pdf}" in findings[0].excerpt
    assert "Figure content must be enclosed" in findings[0].explanation


def test_violating_tikzpicture_outside_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{tikzpicture}\n  \\draw (0,0) -- (1,1);\n\\end{tikzpicture}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1
    assert "\\begin{tikzpicture}" in findings[0].excerpt
    assert "Figure content must be enclosed" in findings[0].explanation


def test_violating_missing_label_in_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/unlabeled.pdf}\n"
        "  \\caption{A figure without a label.}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1
    assert "\\begin{figure}" in findings[0].excerpt
    assert "missing a '\\label'" in findings[0].explanation


def test_violating_missing_label_in_starred_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}[!ht]\n"
        "  \\centering\n"
        "  \\includegraphics{figures/unlabeled.pdf}\n"
        "  \\caption{A starred figure without a label.}\n"
        "\\end{figure*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert "\\begin{figure*}" in findings[0].excerpt
    assert "missing a '\\label'" in findings[0].explanation


def test_violating_unreferenced_figure_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Unreferenced plot.}\n"
        "  \\label{fig:never_used}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert findings[0].line == 5
    assert findings[0].column == 3
    assert "\\label{fig:never_used}" in findings[0].excerpt
    assert "never referenced" in findings[0].explanation


def test_violating_duplicate_figure_labels(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/a.pdf}\n"
        "  \\caption{First figure.}\n"
        "  \\label{fig:duplicate}\n"
        "\\end{figure}\n"
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/b.pdf}\n"
        "  \\caption{Second figure.}\n"
        "  \\label{fig:duplicate}\n"
        "\\end{figure}\n"
        "See \\ref{fig:duplicate} for reference.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 2
    assert all("Duplicate figure label 'fig:duplicate'" in f.explanation for f in findings)
    assert findings[0].line == 5
    assert findings[1].line == 11


def test_cross_file_reference_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    child = tmp_path / "chapter.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/diagram.pdf}\n"
        "  \\caption{Cross-file diagram.}\n"
        "  \\label{fig:diagram}\n"
        "\\end{figure}\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    child.write_text(
        "In this chapter we refer to Figure~\\ref{fig:diagram}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_cross_file_figure_in_child_referenced_in_parent(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    child = tmp_path / "chapter.tex"
    root.write_text(
        "We foreshadow the architecture in Figure~\\autoref{fig:child_diag}.\n\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    child.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/child_diag.pdf}\n"
        "  \\caption{Child diagram.}\n"
        "  \\label{fig:child_diag}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_reference_in_comment_does_not_satisfy_fig_03(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{A plot.}\n"
        "  \\label{fig:unref}\n"
        "\\end{figure}\n"
        "% As seen in Figure~\\ref{fig:unref}, this is commented out.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert "never referenced" in findings[0].explanation


def test_reference_in_verbatim_does_not_satisfy_fig_03(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{A plot.}\n"
        "  \\label{fig:unref}\n"
        "\\end{figure}\n"
        "\\begin{verbatim}\n\\ref{fig:unref}\n\\end{verbatim}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert len(findings) == 1
    assert "never referenced" in findings[0].explanation


def test_same_line_suppression_on_missing_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure} % latex-lint:ignore=FIG-03\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{A plot.}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_same_line_suppression_on_unreferenced_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{A plot.}\n"
        "  \\label{fig:unref} % latex-lint:ignore=FIG-03\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_same_line_suppression_on_outside_content(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\includegraphics{figures/logo.pdf} % latex-lint:ignore=FIG-03\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=FIG-03\n\\includegraphics{figures/logo.pdf}\n% latex-lint:enable=FIG-03\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\includegraphics{figures/logo.pdf}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["FIG-03"])
    assert not any(f.rule_id == "FIG-03" for f in findings)


def test_fig_03_title_macro_logo_allowed(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\addTitleBox{\\includegraphics[width=\\linewidth]{figures/CCPS_logo}}\n"
        "\\titlehead{\\includegraphics{figures/logo.pdf}}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_fig_03_titlepage_environment_allowed(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{titlepage}\n  \\centering\n  \\includegraphics{figures/logo.pdf}\n\\end{titlepage}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_fig_03_preamble_logo_allowed(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\documentclass{article}\n"
        "\\newcommand{\\mylogo}{\\includegraphics{figures/logo.pdf}}\n"
        "\\begin{document}\n"
        "Some text.\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []


def test_fig_03_box_macro_allowed(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\savebox{\\mybox}{\\includegraphics{figures/logo.pdf}}\n\\parbox{5cm}{\\includegraphics{figures/logo.pdf}}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-03"]
    assert findings == []
