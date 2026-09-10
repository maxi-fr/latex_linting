from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_work_03_metadata() -> None:
    rule = get_rule("WORK-03")
    assert rule.rule_id == "WORK-03"
    assert "draft" in rule.explanation.lower()
    assert "twoside" in rule.explanation.lower() or "two-sided" in rule.explanation.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "class defaults" in rule.limits.lower()
    assert "effective page dimensions" in rule.limits.lower()
    assert "complete submission compliance" in rule.limits.lower()


@pytest.mark.parametrize(
    ("source", "expected_opt", "expected_col"),
    [
        (r"\documentclass[draft]{report}", "draft", 16),
        (r"\documentclass[12pt,oneside]{book}", "oneside", 21),
        (r"\documentclass[nohyperref]{scrreprt}", "nohyperref", 16),
        (r"\documentclass[draft=true]{report}", "draft", 16),
    ],
)
def test_work_03_violations(source: str, expected_opt: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    work_03 = [f for f in findings if f.rule_id == "WORK-03"]
    assert len(work_03) == 1
    finding = work_03[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert expected_opt in finding.explanation
    assert expected_opt in finding.correction


def test_work_03_multiple_violations(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = r"\documentclass[draft, oneside]{report}" + "\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    work_03 = [f for f in findings if f.rule_id == "WORK-03"]
    assert len(work_03) == 2
    assert work_03[0].column == 16
    assert work_03[1].column == 23


@pytest.mark.parametrize(
    "source",
    [
        r"\documentclass{report}",
        r"\documentclass[12pt,twoside,a4paper]{report}",
        r"\documentclass[draftcopy,12pt]{report}",
        r"\documentclass[myoneside]{book}",
        r"\documentclass[draft=false]{report}",
        r"\documentclass[draft=off]{report}",
    ],
)
def test_work_03_valid_or_substring_options(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "WORK-03"] == []


def test_work_03_commented_option(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\documentclass[\n  a4paper,\n  % draft,\n  twoside,\n]{report}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "WORK-03"] == []


def test_work_03_multiline_with_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\documentclass[\n  a4paper,\n  draft, % latex-lint:ignore=WORK-03\n  twoside,\n]{report}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "WORK-03"] == []
