from pathlib import Path

from latex_linting.main import check


def test_valid_disable_enable_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04\n"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_enable_without_disable_fails(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:enable=MATH-04\n$\\frac{a}{b}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert any(f.rule_id == "SUPP-02" for f in findings)
    supp_finding = next(f for f in findings if f.rule_id == "SUPP-02")
    assert supp_finding.line == 1
    assert "redundant enable: rule 'MATH-04' is not disabled" in supp_finding.explanation
    assert supp_finding.correction == "Remove the redundant enable directive for 'MATH-04'."


def test_duplicate_disable_fails(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-02"
    assert findings[0].line == 2
    assert "redundant disable: rule 'MATH-04' is already disabled" in findings[0].explanation
    assert findings[0].correction == "Remove the redundant disable directive for 'MATH-04'."


def test_multi_rule_enable_partially_redundant(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=MATH-04\n$\\frac{a}{b}$\n% latex-lint:enable=MATH-04,PROSE-02\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "SUPP-02"
    assert findings[0].line == 3
    assert "redundant enable: rule 'PROSE-02' is not disabled" in findings[0].explanation


def test_supp_02_self_suppression_disable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=SUPP-02\n% latex-lint:enable=MATH-04\n% latex-lint:enable=SUPP-02\n$\\frac{a}{b}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert not any(f.rule_id == "SUPP-02" for f in findings)


def test_supp_02_ignored_via_api(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:enable=MATH-04\n$\\frac{a}{b}$\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root, ignored_rules=["SUPP-02"])
    assert not any(f.rule_id == "SUPP-02" for f in findings)
    assert any(f.rule_id == "MATH-04" for f in findings)
