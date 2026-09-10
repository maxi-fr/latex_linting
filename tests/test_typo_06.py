from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_06_metadata() -> None:
    """Verify TYPO-06 metadata, documentation, examples, and limits in the catalogue."""
    rule = get_rule("TYPO-06")
    assert rule.rule_id == "TYPO-06"
    assert "quotation" in rule.explanation.lower() or "quote" in rule.explanation.lower()
    assert "enquote" in rule.correction.lower() or "``" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "code" in rule.limits.lower() or "verbatim" in rule.limits.lower()


def test_straight_double_quotes_fail(tmp_path: Path) -> None:
    """Detect straight double quotation marks in English prose."""
    root = tmp_path / "thesis.tex"
    source = '\\section{Introduction}\nThis is a "quoted" term.\nWe note that "results" vary.\n'
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert len(findings) == 4
    for finding in findings:
        assert finding.rule_id == "TYPO-06"
        assert "``" in finding.correction or "enquote" in finding.correction


def test_straight_single_quotes_fail(tmp_path: Path) -> None:
    """Detect straight single quotes used as quotation marks in English prose."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Introduction}\nThis is a 'single-quoted' word.\nHe stated: 'Results are preliminary.'\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert len(findings) >= 2
    for finding in findings:
        assert finding.rule_id == "TYPO-06"


def test_latex_quotation_marks_pass(tmp_path: Path) -> None:
    """Permit valid LaTeX quotation marks and enquote commands."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Introduction}\n"
        "This is a ``double-quoted'' phrase.\n"
        "This is a `single-quoted' phrase.\n"
        "This is an \\enquote{enquoted phrase} in text.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_contractions_and_possessives_pass(tmp_path: Path) -> None:
    """Permit apostrophes in contractions and singular or plural possessives."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Grammar}\n"
        "Don't assume it's impossible when we haven't tried.\n"
        "The author's model improves the system's performance.\n"
        "We analyzed students' projects and users' feedback.\n"
        "O'Connor developed this method.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_math_mode_prime_and_quotes_pass(tmp_path: Path) -> None:
    """Permit prime symbols and quotes in math mode."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Formulas}\n"
        "We compute the derivative $f'(x)$ and second derivative $f''(x)$.\n"
        "In math, let $x = \"label\"$ or $y = 'a'$.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_escaped_accent_commands_pass(tmp_path: Path) -> None:
    """Permit escaped accent commands with quotation marks and apostrophes."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Names}\n"
        'Names include Schr\\"odinger, G\\"odel, and M\\"uller.\n'
        "Also Caf\\'e, Poincar\\'e, and \\`a la carte.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_literal_code_excluded(tmp_path: Path) -> None:
    """Exclude literal code environments and verb commands from TYPO-06 checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Source Code}\n"
        "\\verb|\"hello\"| and \\verb|'world'| are code.\n"
        "\\begin{verbatim}\n"
        'print("hello world")\n'
        "val = 'test'\n"
        "\\end{verbatim}\n"
        "\\begin{lstlisting}\n"
        'String s = "example";\n'
        "\\end{lstlisting}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_comments_excluded(tmp_path: Path) -> None:
    """Exclude comments containing straight quotes from TYPO-06 checks."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Comments}\n% \"quoted\" and 'single' in comments\nRegular text without quotes.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Suppress TYPO-06 on the matching source line with a directive."""
    root = tmp_path / "thesis.tex"
    source = '\\section{Suppression}\nThis is "quoted".\nThis is "ignored". % latex-lint:ignore=TYPO-06\n'
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert len(findings) == 2
    for finding in findings:
        assert finding.line == 2


def test_disable_enable_suppression(tmp_path: Path) -> None:
    """Respect disable and enable directives for TYPO-06."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Suppression}\n"
        "% latex-lint:disable=TYPO-06\n"
        'This is "ignored".\n'
        "% latex-lint:enable=TYPO-06\n"
        'This is "flagged".\n'
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-06"]
    assert len(findings) == 2
    for finding in findings:
        assert finding.line == 5
