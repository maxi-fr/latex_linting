from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_03_metadata() -> None:
    rule = get_rule("TYPO-03")
    assert rule.rule_id == "TYPO-03"
    assert "thin space" in rule.explanation.lower()
    assert "\\," in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "abbreviation" in rule.limits.lower()


def test_valid_abbreviations_thin_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "Consider, e.\\,g., standard models.\n"
        "This holds, i.\\,e., without loss of generality.\n"
        "At sentence start, E.\\,g. and I.\\,e. also use thin space.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert findings == []


def test_invalid_abbreviations_no_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "Consider, e.g., standard models.\n"
        "This holds, i.e., without loss of generality.\n"
        "Capitalized: E.g., for example, and I.e., that is.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert len(findings) == 4
    assert findings[0].rule_id == "TYPO-03"
    assert findings[0].line == 1
    assert findings[0].column == 11
    assert "e.g." in findings[0].excerpt


def test_invalid_abbreviations_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "Consider, e. g., standard models.\n"
        "This holds, i. e., without loss of generality.\n"
        "Capitalized: E. g., for example, and I. e., that is.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert len(findings) == 4


def test_invalid_abbreviations_tilde_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "Consider, e.~g., standard models.\nThis holds, i.~e., without loss of generality.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert len(findings) == 2


def test_substrings_and_commands_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "Visit college.edu or see \\eg and \\ie commands.\n\\url{https://example.com/e.g./test}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert findings == []


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "% e.g. in a comment\n\\begin{verbatim}\ne.g. in verbatim\ni.e. in verbatim\n\\end{verbatim}\n\\verb|e.g.|\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert findings == []


def test_math_mode_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("$e.g.$ and $i.e.$\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert findings == []


def test_same_line_ignore_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("Use e.g. here % latex-lint:ignore=TYPO-03\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=TYPO-03\ne.g. here\n% latex-lint:enable=TYPO-03\ni.e. here\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-03"]
    assert len(findings) == 1
    assert findings[0].line == 4
