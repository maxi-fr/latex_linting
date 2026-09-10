from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_07_metadata() -> None:
    """Verify TYPO-07 metadata, documentation, examples, and limits in the catalogue."""
    rule = get_rule("TYPO-07")
    assert rule.rule_id == "TYPO-07"
    assert "emphasis" in rule.explanation.lower() or "font" in rule.explanation.lower()
    assert "emph" in rule.correction.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "underline" in rule.limits.lower() or "nested" in rule.limits.lower()


def test_underline_in_text_fails(tmp_path: Path) -> None:
    """Detect underline command used in text mode."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Styling}\nThis is \\underline{forbidden} styling in academic text.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-07"
    assert "underline" in findings[0].explanation.lower()
    assert "\\emph" in findings[0].correction


def test_bold_in_running_prose_fails(tmp_path: Path) -> None:
    """Detect bold command used for emphasis in running prose."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Discussion}\nWe note that this result is \\textbf{critically important}.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-07"
    assert "bold" in findings[0].explanation.lower()
    assert "\\emph" in findings[0].correction


def test_bold_in_table_passes(tmp_path: Path) -> None:
    """Permit bold formatting in table headers and cells."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Data}\n"
        "\\begin{tabular}{ll}\n"
        "\\toprule\n"
        "\\textbf{Parameter} & \\textbf{Value} \\\\\n"
        "\\midrule\n"
        "Alpha & 1.0 \\\\\n"
        "\\bottomrule\n"
        "\\end{tabular}\n"
        "\\begin{tabularx}{\\textwidth}{ll}\n"
        "\\textbf{Column A} & \\textbf{Column B} \\\\\n"
        "\\end{tabularx}\n"
        "\\begin{longtable}{ll}\n"
        "\\textbf{Col 1} & \\textbf{Col 2} \\\\\n"
        "\\end{longtable}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert findings == []


def test_bold_in_prose_after_table_fails(tmp_path: Path) -> None:
    """Detect bold emphasis in prose immediately following a table."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Data}\n"
        "\\begin{tabular}{ll}\n"
        "\\textbf{Param} & \\textbf{Val} \\\\\n"
        "\\end{tabular}\n"
        "This is \\textbf{bold} emphasis following the table.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].line == 5


def test_bold_in_prose_after_math_fails(tmp_path: Path) -> None:
    """Detect bold emphasis in prose immediately following displayed math."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Analysis}\n"
        "\\begin{equation}\n"
        "  E = mc^2\n"
        "\\end{equation}\n"
        "We observe \\textbf{high divergence} after the equation.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].line == 5


def test_nested_font_attributes_fail(tmp_path: Path) -> None:
    """Detect combinations of multiple font attributes including nested commands."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Emphasis}\n"
        "Combined \\textbf{\\textit{bold and italic}} text.\n"
        "Combined \\textbf{\\emph{bold and emph}} text.\n"
        "Combined \\emph{\\textbf{emph and bold}} text.\n"
        "Combined \\underline{\\emph{underline and emph}} text.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) >= 4
    for finding in findings:
        assert finding.rule_id == "TYPO-07"


def test_nested_emphasis_in_table_fails(tmp_path: Path) -> None:
    """Detect combined font attributes even within table environments."""
    root = tmp_path / "thesis.tex"
    source = "\\begin{tabular}{ll}\n\\textbf{\\textit{Both}} & Value \\\\\n\\end{tabular}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert "combine" in findings[0].explanation.lower() or "multiple" in findings[0].explanation.lower()


def test_single_emphasis_passes(tmp_path: Path) -> None:
    """Permit single textual emphasis using emph or textit."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Proper Emphasis}\n"
        "We use \\emph{proper emphasis} in running text.\n"
        "We can also use \\textit{italicized terms} without combining.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert findings == []


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    """Exclude comments and literal environments from TYPO-07 checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Code}\n"
        "% \\underline{comment} and \\textbf{bold in comment}\n"
        "\\verb|\\underline{code}| and \\verb|\\textbf{code}|\n"
        "\\begin{verbatim}\n"
        "\\underline{verbatim} \\textbf{\\textit{code}}\n"
        "\\end{verbatim}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert findings == []


def test_math_mode_excluded(tmp_path: Path) -> None:
    """Exclude math mode bold and underline constructs."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Math}\nLet $\\mathbf{x} = [1, 2]^T$ and $\\underline{x}$ denote vectors.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Suppress TYPO-07 on the matching source line with a directive."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Suppression}\n"
        "This is \\underline{flagged}.\n"
        "This is \\underline{ignored}. % latex-lint:ignore=TYPO-07\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].line == 2


def test_disable_enable_suppression(tmp_path: Path) -> None:
    """Respect disable and enable directives for TYPO-07."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Suppression}\n"
        "% latex-lint:disable=TYPO-07\n"
        "This is \\underline{ignored} and \\textbf{ignored}.\n"
        "% latex-lint:enable=TYPO-07\n"
        "This is \\underline{flagged}.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-07"]
    assert len(findings) == 1
    assert findings[0].line == 5
