from pathlib import Path

from latex_linting.main import check


def test_valid_image_caption_label_order(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{A figure with correct element order.}\n"
        "  \\label{fig:plot}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:plot}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_valid_tikzpicture_order(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\begin{tikzpicture}\n"
        "    \\draw (0,0) -- (1,1);\n"
        "  \\end{tikzpicture}\n"
        "  \\caption{A TikZ diagram.}\n"
        "  \\label{fig:tikz}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:tikz}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_valid_label_inside_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption with nested label.\\label{fig:nested}}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:nested}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_valid_multiple_images_preceding_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/left.pdf}\n"
        "  \\includegraphics{figures/right.pdf}\n"
        "  \\caption{Two plots placed side by side.}\n"
        "  \\label{fig:two}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:two}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_valid_input_tikz_order(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    tikz_file = tmp_path / "plot.tikz"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\input{plot.tikz}\n"
        "  \\caption{TikZ plot from included file.}\n"
        "  \\label{fig:included}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:included}.\n",
        encoding="utf-8",
    )
    tikz_file.write_text("\\draw (0,0) -- (1,0);\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_violating_caption_precedes_image(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{Caption placed before the image.}\n"
        "  \\label{fig:wrong}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:wrong}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert len(findings) == 1
    assert findings[0].line == 3
    assert findings[0].column == 3
    assert "\\caption" in findings[0].excerpt
    assert "below the figure image content" in findings[0].explanation


def test_violating_caption_precedes_tikzpicture(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{Caption placed before tikzpicture.}\n"
        "  \\label{fig:wrong_tikz}\n"
        "  \\begin{tikzpicture}\n"
        "    \\draw (0,0) -- (1,1);\n"
        "  \\end{tikzpicture}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:wrong_tikz}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert len(findings) == 1
    assert findings[0].line == 3
    assert "\\caption" in findings[0].excerpt
    assert "below the figure image content" in findings[0].explanation


def test_violating_label_precedes_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\label{fig:premature}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\caption{Caption placed after label.}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:premature}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert len(findings) == 1
    assert findings[0].line == 3
    assert findings[0].column == 3
    assert "\\label{fig:premature}" in findings[0].excerpt
    assert "inside or after '\\caption'" in findings[0].explanation


def test_violating_label_between_image_and_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\label{fig:between}\n"
        "  \\caption{Caption after label.}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:between}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert len(findings) == 1
    assert findings[0].line == 4
    assert "\\label{fig:between}" in findings[0].excerpt
    assert "inside or after '\\caption'" in findings[0].explanation


def test_violating_both_caption_before_image_and_label_before_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\label{fig:inverted}\n"
        "  \\caption{Caption in inverted figure.}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:inverted}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert len(findings) == 2
    assert any("inside or after '\\caption'" in f.explanation for f in findings)
    assert any("below the figure image content" in f.explanation for f in findings)


def test_same_line_suppression_on_caption(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{Top caption.} % latex-lint:ignore=FIG-07\n"
        "  \\label{fig:top}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:top}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_same_line_suppression_on_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "  \\label{fig:early} % latex-lint:ignore=FIG-07\n"
        "  \\caption{Bottom caption.}\n"
        "\\end{figure}\n"
        "See Figure~\\ref{fig:early}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=FIG-07\n"
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{Top caption.}\n"
        "  \\label{fig:top}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "\\end{figure}\n"
        "% latex-lint:enable=FIG-07\n"
        "See Figure~\\ref{fig:top}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FIG-07"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{Top caption.}\n"
        "  \\label{fig:top}\n"
        "  \\includegraphics{figures/plot.pdf}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["FIG-07"])
    assert not any(f.rule_id == "FIG-07" for f in findings)
