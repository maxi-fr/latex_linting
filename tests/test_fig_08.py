from pathlib import Path

from latex_linting.main import check


def test_valid_figure_with_centering(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Centered plot.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert findings == []


def test_valid_starred_figure_with_centering(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/wide.pdf}\n"
        "  \\caption{Wide centered plot.}\n"
        "  \\label{fig:wide}\n"
        "\\end{figure*}\n"
        "See Figure~\\ref{fig:wide}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert findings == []


def test_violating_center_environment_in_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\begin{center}\n"
        "    \\includegraphics{figures/plot.pdf}\n"
        "  \\end{center}\n"
        "  \\caption{Plot with center environment.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].column == 3
    assert "\\begin{center}" in findings[0].excerpt
    assert "Do not use the 'center' environment" in findings[0].explanation


def test_violating_center_environment_in_starred_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}\n"
        "  \\begin{center}\n"
        "    \\includegraphics{figures/wide.pdf}\n"
        "  \\end{center}\n"
        "  \\caption{Starred plot with center environment.}\n"
        "  \\label{fig:wide}\n"
        "\\end{figure*}\n"
        "See Figure~\\ref{fig:wide}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert len(findings) == 1
    assert findings[0].line == 2
    assert "\\begin{center}" in findings[0].excerpt


def test_violating_missing_centering_in_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Uncentered plot.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1
    assert "\\begin{figure}" in findings[0].excerpt
    assert "missing a '\\centering' declaration" in findings[0].explanation


def test_violating_missing_centering_in_starred_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}\n"
        "  \\includegraphics{figures/wide.pdf}\n"
        "  \\caption{Uncentered wide plot.}\n"
        "  \\label{fig:wide}\n"
        "\\end{figure*}\n"
        "See Figure~\\ref{fig:wide}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert "\\begin{figure*}" in findings[0].excerpt
    assert "missing a '\\centering' declaration" in findings[0].explanation


def test_same_line_suppression_on_center_env(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\begin{center} % latex-lint:ignore=FIG-08\n"
        "    \\includegraphics{figures/plot.pdf}\n"
        "  \\end{center}\n"
        "  \\caption{Plot with suppressed center environment.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert findings == []


def test_same_line_suppression_on_missing_centering(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure} % latex-lint:ignore=FIG-08\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Uncentered plot.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=FIG-08\n"
        "\\begin{figure}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Uncentered plot.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "% latex-lint:enable=FIG-08\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-08"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Uncentered plot.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["FIG-08"])
    assert not any(f.rule_id == "FIG-08" for f in findings)
