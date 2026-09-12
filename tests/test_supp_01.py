from pathlib import Path

from latex_linting.main import check


def test_ignore_with_violation_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    assert check(root) == []


def test_ignore_without_violation_fails(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-01"
    assert findings[0].line == 1
    assert "MATH-04" in findings[0].explanation
    assert "Remove 'MATH-04' from the directive" in findings[0].correction


def test_ignore_multi_rule_one_unused(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$ % latex-lint:ignore=MATH-04,PROSE-02", encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-01"
    assert "PROSE-02" in findings[0].explanation
    assert findings[0].correction == "Remove 'PROSE-02' from the directive."


def test_ignore_multi_rule_both_unused(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$ % latex-lint:ignore=MATH-04,PROSE-02", encoding="utf-8")
    findings = check(root)
    assert len(findings) == 2
    assert {f.rule_id for f in findings} == {"SUPP-01"}
    explanations = {f.explanation for f in findings}
    assert "unused suppression for rule 'MATH-04'" in explanations
    assert "unused suppression for rule 'PROSE-02'" in explanations


def test_disable_with_violation_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04\n"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_disable_without_violation_fails(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$a/b$\n% latex-lint:enable=MATH-04\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-01"
    assert findings[0].line == 1
    assert "MATH-04" in findings[0].explanation


def test_disable_to_eof_without_violation_fails(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$a/b$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-01"
    assert findings[0].line == 1
    assert "MATH-04" in findings[0].explanation


def test_disable_multi_rule_one_unused(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04,PROSE-02\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04,PROSE-02\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-01"
    assert findings[0].line == 1
    assert "PROSE-02" in findings[0].explanation
    assert findings[0].correction == "Remove 'PROSE-02' from the disable directive."


def test_supp_01_self_suppression_same_line(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$ % latex-lint:ignore=MATH-04,SUPP-01", encoding="utf-8")
    assert check(root) == []


def test_supp_01_self_suppression_disable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=SUPP-01\n$a/b$ % latex-lint:ignore=MATH-04\n% latex-lint:enable=SUPP-01\n"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_supp_01_ignored_via_api(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    assert check(root, ignored_rules=["SUPP-01"]) == []


def test_supp_01_rule_in_ignored_rules_not_flagged_as_unused(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    assert check(root, ignored_rules=["MATH-04"]) == []
