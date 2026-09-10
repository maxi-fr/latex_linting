from pathlib import Path

from latex_linting.main import check


def test_valid_figure_with_caption_full_stop(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{This is a full caption ending with a full stop.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_valid_figure_with_label_inside_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption text ending with period.\\label{fig:plot}}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_valid_optional_short_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption[Short title]{Long caption text ending in a full stop.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_valid_multiline_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{\n"
        "    First sentence of the caption.\n"
        "    Second sentence describing the curves.\n"
        "  }\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_valid_caption_with_nested_formatting(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Comparison between \\textbf{Algorithm A} and \\emph{Algorithm B}.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_valid_starred_figure(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/wide.pdf}\n"
        "  \\caption{Wide figure caption with full stop.}\n"
        "  \\label{fig:wide}\n"
        "\\end{figure*}\n"
        "Figure~\\ref{fig:wide} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_violating_missing_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 1
    assert "\\begin{figure}" in findings[0].excerpt
    assert "missing a '\\caption'" in findings[0].explanation


def test_violating_caption_missing_full_stop(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption text without a terminal full stop}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert findings[0].column == 3
    assert "\\caption" in findings[0].excerpt
    assert "must end with a full stop" in findings[0].explanation


def test_violating_caption_short_has_dot_but_main_lacks_dot(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption[Short title.]{Main caption text without terminal dot}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert "must end with a full stop" in findings[0].explanation


def test_violating_caption_with_label_inside_lacking_dot(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption text without period\\label{fig:plot}}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert "must end with a full stop" in findings[0].explanation


def test_violating_empty_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert "must end with a full stop" in findings[0].explanation


def test_same_line_suppression_on_missing_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure} % latex-lint:ignore=FIG-06\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_same_line_suppression_on_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Formula without dot} % latex-lint:ignore=FIG-06\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=FIG-06\n"
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption without dot}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "% latex-lint:enable=FIG-06\n"
        "Figure~\\ref{fig:plot} shows the outcome.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-06"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption without dot}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["FIG-06"])
    assert not any(f.rule_id == "FIG-06" for f in findings)
