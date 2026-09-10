from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_04_metadata() -> None:
    rule = get_rule("TYPO-04")
    assert rule.rule_id == "TYPO-04"
    assert "swallow" in rule.explanation.lower()
    assert "{}" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "\\latex" in rule.limits.lower()


def test_valid_commands_with_explicit_terminators(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "We use \\LaTeX{} for formatting.\n"
        "Knuth created \\TeX\\ in the 1970s.\n"
        "References use \\BibTeX~as well.\n"
        "Smith \\etal{} found this.\n"
        "Consider \\eg{} these cases.\n"
        "This implies \\ie{} that the bound holds.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_valid_commands_followed_by_punctuation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "This thesis was prepared using \\LaTeX.\n"
        "With \\LaTeX, typesetting is easier.\n"
        "Consider the tools: \\LaTeX: modern and robust.\n"
        "We compared \\TeX; however, others differ.\n"
        "We love \\LaTeX!\n"
        "Have you used \\BibTeX?\n"
        "The system (implemented in \\LaTeX) works well.\n"
        "Bracketed [using \\BibTeX] citations work.\n"
        "Enclosed in braces {\\TeX} is valid.\n"
        "A \\LaTeX-based tool was developed.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_valid_command_at_end_of_file(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("Written in \\LaTeX", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_invalid_commands_swallowed_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "We use \\LaTeX is our main system.\n"
        "Knuth designed \\TeX was revolutionary.\n"
        "Managing references with \\BibTeX is standard.\n"
        "Smith \\etal proposed this method.\n"
        "Consider \\eg the following.\n"
        "This holds \\ie without doubt.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert len(findings) == 6
    assert findings[0].rule_id == "TYPO-04"
    assert findings[0].line == 1
    assert findings[0].column == 8
    assert "\\LaTeX" in findings[0].excerpt


def test_invalid_commands_swallowed_newline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "We use \\LaTeX\nto format our documents.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 8


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "% \\LaTeX is great\n"
        "\\begin{verbatim}\n"
        "\\LaTeX is great\n"
        "\\TeX is great\n"
        "\\end{verbatim}\n"
        "\\verb|\\LaTeX is great|\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_math_mode_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("$\\LaTeX is$ and $\\TeX is$\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_syntax_command_arguments_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\url{https://example.com/\\LaTeX/is/cool}\n\\label{\\LaTeX is}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_same_line_ignore_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("\\LaTeX is great % latex-lint:ignore=TYPO-04\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=TYPO-04\n\\LaTeX is great\n% latex-lint:enable=TYPO-04\n\\TeX is great\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-04"]
    assert len(findings) == 1
    assert findings[0].line == 4
