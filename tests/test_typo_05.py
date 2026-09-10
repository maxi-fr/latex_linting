from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_05_metadata() -> None:
    """Verify TYPO-05 metadata, documentation, examples, and limits in the catalogue."""
    rule = get_rule("TYPO-05")
    assert rule.rule_id == "TYPO-05"
    assert "dash" in rule.explanation.lower() or "hyphen" in rule.explanation.lower()
    assert "--" in rule.correction or "math" in rule.correction.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "compound" in rule.limits.lower() or "math" in rule.limits.lower()


def test_numeric_range_single_hyphen_fails(tmp_path: Path) -> None:
    """Detect single hyphens used for numeric ranges in text mode."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Evaluation}\n"
        "We tested values from 10-20 units.\n"
        "Results are shown on pp. 5-10 and pages 12-15.\n"
        "A total of 100-200 samples were collected.\n"
        "Ranges like 10 - 20 also appear.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert len(findings) == 5
    for finding in findings:
        assert finding.rule_id == "TYPO-05"
        assert "--" in finding.correction


def test_numeric_range_en_dash_passes(tmp_path: Path) -> None:
    """Permit valid en-dash numeric ranges in text mode."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Evaluation}\n"
        "We tested values from 10--20 units.\n"
        "Results are shown on pp. 5--10 and pages 12--15.\n"
        "A total of 100--200 samples were collected.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_em_dash_and_german_gedankenstrich_pass(tmp_path: Path) -> None:
    """Permit em-dashes and spaced en-dashes in prose."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Background}\n"
        "Words---without spaces---are separated by em-dashes.\n"
        "In German prose, Wort -- Wort uses spaced en-dashes.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_negative_number_text_hyphen_fails(tmp_path: Path) -> None:
    """Detect text hyphens used for negative numbers in prose."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Experiments}\n"
        "The temperature dropped to -5 degrees Celsius.\n"
        "We observed offsets of -10 and -20 across runs.\n"
        "Values within (-5) and [-10] were recorded.\n"
        "-5 is the initial setpoint.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert len(findings) == 6
    for finding in findings:
        assert finding.rule_id == "TYPO-05"
        assert "$" in finding.correction or "--" in finding.correction


def test_negative_number_math_mode_passes(tmp_path: Path) -> None:
    """Permit negative numbers and minus signs in math mode."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Experiments}\n"
        "The temperature dropped to $-5$ degrees Celsius.\n"
        "We observed offsets of $-10$ and $-20$ across runs.\n"
        "We compute $x - y$ and $-5 - 10$ in math mode.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_compound_words_pass(tmp_path: Path) -> None:
    """Permit hyphens in compound words and non-range alphanumeric expressions."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Related Work}\n"
        "We develop a state-of-the-art closed-loop controller.\n"
        "It handles high-dimensional decision-making problems.\n"
        "Consider COVID-19, ISO-9001 standards, and x86-64 architecture.\n"
        "We also test 10-fold cross-validation, top-10 models, and 3-way splits.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    """Exclude comments and literal environments from TYPO-05 checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Implementation}\n"
        "% 10-20 and -5 in comments are ignored\n"
        "\\verb|10-20| and \\verb|-5| are literal.\n"
        "\\begin{verbatim}\n"
        "Range: 10-20, Negative: -5\n"
        "\\end{verbatim}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_syntax_command_arguments_excluded(tmp_path: Path) -> None:
    """Exclude non-prose syntax command arguments from TYPO-05 checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{References}\n"
        "\\label{sec:10-20}\n"
        "See Section~\\ref{sec:10-20}.\n"
        "Refer to~\\cite{smith-2020}.\n"
        "Visit \\url{https://example.com/item-10-20}.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Suppress TYPO-05 on the matching source line with a directive."""
    root = tmp_path / "thesis.tex"
    source = "\\section{Suppression}\nRange 10-20 is checked.\nRange 10-20 is ignored. % latex-lint:ignore=TYPO-05\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert len(findings) == 1
    assert findings[0].line == 2


def test_disable_enable_suppression(tmp_path: Path) -> None:
    """Respect disable and enable directives for TYPO-05."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Suppression}\n"
        "% latex-lint:disable=TYPO-05\n"
        "Range 10-20 and -5 are ignored.\n"
        "% latex-lint:enable=TYPO-05\n"
        "Range 10-20 is flagged.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-05"]
    assert len(findings) == 1
    assert findings[0].line == 5
