from pathlib import Path

import pytest

from latex_linting.main import check


def test_ignore_suppresses_same_line(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    assert check(root) == []


def test_ignore_whitespace_variations(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$ %   latex-lint : ignore = MATH-04  ", encoding="utf-8")
    assert check(root) == []


def test_ignore_multiple_violations_on_same_line(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b} + \frac{c}{d}$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    assert check(root) == []


def test_ignore_does_not_suppress_following_line(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("% latex-lint:ignore=MATH-04\n$\\frac{a}{b}$", encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert (findings[0].line, findings[0].column) == (2, 2)


def test_ignore_on_first_line_preserves_second_line_finding(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("$\\frac{a}{b}$ % latex-lint:ignore=MATH-04\n$\\frac{c}{d}$", encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert (findings[0].line, findings[0].column) == (2, 2)


def test_disable_applies_until_enable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04\n$\\frac{c}{d}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert (findings[0].line, findings[0].column) == (4, 2)


def test_disable_applies_until_end_of_file(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n$\\frac{c}{d}$\n"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_disable_from_directive_position(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "$\\frac{a}{b}$\n% latex-lint:disable=MATH-04\n$\\frac{c}{d}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert (findings[0].line, findings[0].column) == (1, 2)


def test_disable_on_same_line_after_violation_does_not_suppress_earlier_violation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "$\\frac{a}{b}$ % latex-lint:disable=MATH-04\n$\\frac{c}{d}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert (findings[0].line, findings[0].column) == (1, 2)


def test_literal_code_directives_have_no_suppression_effect(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\begin{verbatim}\n"
        "% latex-lint:disable=MATH-04\n"
        "\\end{verbatim}\n"
        "$\\frac{a}{b}$\n"
        "\\begin{lstlisting}\n"
        "% latex-lint:ignore=MATH-04\n"
        "\\end{lstlisting}\n"
        "\\verb|% latex-lint:disable=MATH-04|\n"
        "\\% latex-lint:disable=MATH-04\n"
        "$\\frac{c}{d}$\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 2
    assert [finding.line for finding in findings] == [4, 10]


def test_literal_code_with_unknown_rule_id_is_ignored(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\begin{verbatim}\n% latex-lint:ignore=UNKNOWN-99\n\\end{verbatim}\n"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_unknown_rule_id_in_source_directive_raises_value_error(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("% latex-lint:ignore=UNKNOWN\n", encoding="utf-8")
    with pytest.raises(ValueError, match="UNKNOWN"):
        check(root)


def test_unknown_action_in_source_directive_raises_value_error(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("% latex-lint:invalid_action=MATH-04\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid_action"):
        check(root)


def test_malformed_directive_raises_value_error(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("% latex-lint:ignore\n", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed"):
        check(root)


def test_ordinary_comment_mentioning_latex_lint_is_not_directive(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% Here latex-lint is mentioned in normal prose\n$\\frac{a}{b}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].line == 2


def test_api_ignored_rules(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$", encoding="utf-8")
    assert check(root, ignored_rules=["MATH-04"]) == []
    assert check(root, ignored_rules={"MATH-04"}) == []
    assert check(root, ignored_rules=("MATH-04",)) == []
    assert len(check(root, ignored_rules=[])) == 1
    assert len(check(root, ignored_rules=None)) == 1


def test_api_ignored_rules_cannot_be_undone_by_enable_directive(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:enable=MATH-04\n$\\frac{a}{b}$\n"
    root.write_text(source, encoding="utf-8")
    assert check(root, ignored_rules=["MATH-04"]) == []


def test_api_unknown_rule_id_in_ignored_rules(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$", encoding="utf-8")
    with pytest.raises(ValueError, match="UNKNOWN"):
        check(root, ignored_rules=["UNKNOWN"])
