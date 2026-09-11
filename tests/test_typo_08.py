from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_08_metadata() -> None:
    """Verify TYPO-08 metadata, documentation, examples, and limits in the catalogue."""
    rule = get_rule("TYPO-08")
    assert rule.rule_id == "TYPO-08"
    assert "break" in rule.explanation.lower() or "line" in rule.explanation.lower()
    assert "blank" in rule.correction.lower() or "paragraph" in rule.correction.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "table" in rule.limits.lower() or "math" in rule.limits.lower()


def test_double_backslash_in_prose_fails(tmp_path: Path) -> None:
    """Detect double backslash line breaks in running prose."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Prose}\n"
        "First sentence in the paragraph.\\\\\n"
        "Second sentence following a double backslash.\n"
        "Another sentence with spacing.\\\\[1em]\n"
        "Continuing on the next line.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 2
    for finding in findings:
        assert finding.rule_id == "TYPO-08"
        assert "blank line" in finding.correction.lower()


def test_newline_in_prose_fails(tmp_path: Path) -> None:
    """Detect newline command in running prose."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Prose}\nFirst sentence in the paragraph.\\newline\nSecond sentence following newline command.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-08"


def test_linebreak_in_prose_fails(tmp_path: Path) -> None:
    """Detect linebreak command in running prose."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Prose}\n"
        "First sentence in the paragraph.\\linebreak\n"
        "Second sentence following linebreak command.\n"
        "Third sentence with optional arg.\\linebreak[4]\n"
        "Continuing after optional linebreak.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 2
    for finding in findings:
        assert finding.rule_id == "TYPO-08"


def test_row_breaks_in_tables_pass(tmp_path: Path) -> None:
    """Permit row breaks in supported table environments."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Tables}\n"
        "\\begin{tabular}{ll}\n"
        "A & B \\\\\n"
        "C & D \\\\\n"
        "\\end{tabular}\n"
        "\\begin{tabularx}{\\textwidth}{ll}\n"
        "E & F \\\\\n"
        "\\end{tabularx}\n"
        "\\begin{longtable}{ll}\n"
        "G & H \\\\\n"
        "\\end{longtable}\n"
        "\\begin{tabular*}{10cm}{ll}\n"
        "I & J \\\\\n"
        "\\end{tabular*}\n"
        "\\begin{tabulary}{\\textwidth}{ll}\n"
        "K & L \\\\\n"
        "\\end{tabulary}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []


def test_multiline_math_breaks_pass(tmp_path: Path) -> None:
    """Permit line breaks in supported multiline math environments."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Math}\n"
        "\\begin{align}\n"
        "  x &= 1 \\\\\n"
        "  y &= 2\n"
        "\\end{align}\n"
        "\\begin{gather}\n"
        "  a = b \\\\\n"
        "  c = d\n"
        "\\end{gather}\n"
        "\\begin{multline}\n"
        "  e + f \\\\\n"
        "  + g\n"
        "\\end{multline}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []


def test_title_and_author_macros_pass(tmp_path: Path) -> None:
    """Permit line breaks in title, author, subtitle, institute, and date macros."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\title{Thesis Title \\\\ Subtitle}\n"
        "\\author{First Author \\\\ Second Author}\n"
        "\\subtitle{Part 1 \\\\ Part 2}\n"
        "\\institute{Institute 1 \\\\ Institute 2}\n"
        "\\date{September 2026 \\\\ Version 1.0}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []


def test_prose_after_table_fails(tmp_path: Path) -> None:
    """Detect line breaks in prose immediately following a table."""
    root = tmp_path / "thesis.tex"
    source = "\\begin{tabular}{ll}\nA & B \\\\\n\\end{tabular}\nProse after table.\\\\\nNext sentence.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_prose_after_math_fails(tmp_path: Path) -> None:
    """Detect line breaks in prose immediately following displayed math."""
    root = tmp_path / "thesis.tex"
    source = "\\begin{align}\n  x &= 1 \\\\\n\\end{align}\nProse after math.\\\\\nNext sentence.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    """Exclude comments and literal environments from TYPO-08 checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Code}\n"
        "% Line break \\\\ in comment\n"
        "% \\newline in comment\n"
        "\\verb|\\\\| and \\verb|\\newline| are literal.\n"
        "\\begin{verbatim}\n"
        "Line 1 \\\\\n"
        "Line 2 \\newline\n"
        "\\end{verbatim}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Suppress TYPO-08 on the matching source line with a directive."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Suppression}\nThis is flagged.\\\\\nThis is ignored.\\\\ % latex-lint:ignore=TYPO-08\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 1
    assert findings[0].line == 2


def test_disable_enable_suppression(tmp_path: Path) -> None:
    """Respect disable and enable directives for TYPO-08."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Suppression}\n"
        "% latex-lint:disable=TYPO-08\n"
        "Line 1\\\\ \n"
        "Line 2\\newline\n"
        "% latex-lint:enable=TYPO-08\n"
        "Line 3\\\\\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert len(findings) == 1
    assert findings[0].line == 6


def test_koma_and_university_title_macros_pass(tmp_path: Path) -> None:
    """Permit line breaks in KOMA-Script and university title macros."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\lowertitleback{TU Darmstadt\\\\\nInstitut für Automatisierungstechnik\\\\\n}\n"
        "\\uppertitleback{Upper line 1\\\\\nUpper line 2}\n"
        "\\dedication{To my family\\\\\nand friends}\n"
        "\\publishers{Publisher 1\\\\\nPublisher 2}\n"
        "\\reviewer{Reviewer 1\\\\\nReviewer 2}\n"
        "\\reviewer*[Supervisor]{Examiner 1\\\\\nExaminer 2}\n"
        "\\supervisor{Supervisor 1\\\\\nSupervisor 2}\n"
        "\\titlehead{Head 1\\\\\nHead 2}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []


def test_titlepage_environment_breaks_pass(tmp_path: Path) -> None:
    """Permit line breaks inside titlepage environment."""
    root = tmp_path / "thesis.tex"
    source = "\\begin{titlepage}\nTitle line 1\\\\\nTitle line 2\\\\\n\\end{titlepage}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-08"]
    assert findings == []
