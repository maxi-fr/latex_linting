from pathlib import Path

import pytest

from latex_linting.cli import main as cli_main
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_cite_09_metadata() -> None:
    rule = get_rule("CITE-09")
    assert rule.rule_id == "CITE-09"
    assert rule.enabled_by_default is False
    assert "cite-checked" in rule.explanation
    assert "cite-checked" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "off by default" in rule.limits.lower() or "default" in rule.limits.lower()


def test_cite_09_off_by_default(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("This method was proven effective~\\cite{smith2020}.\n", encoding="utf-8")
    assert check(root) == []

    findings_rule = check(root, rule_filter=["CITE-09"])
    assert len(findings_rule) == 1
    assert findings_rule[0].rule_id == "CITE-09"
    assert "smith2020" in findings_rule[0].explanation

    findings_enabled = check(root, enabled_rules=["CITE-09"])
    assert len(findings_enabled) == 1
    assert findings_enabled[0].rule_id == "CITE-09"


@pytest.mark.parametrize(
    ("text", "expected_col", "expected_key"),
    [
        ("This method is effective~\\cite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\citep[p.~5]{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\citet[see][p.~10]{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\autocite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\parencite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\footcite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\textcite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\fullcite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\nocite{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\citeauthor{smith2020}.", 26, "smith2020"),
        ("This method is effective~\\citeyear{smith2020}.", 26, "smith2020"),
    ],
)
def test_cite_09_violations(text: str, expected_col: int, expected_key: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(text + "\n", encoding="utf-8")
    findings = check(root, rule_filter=["CITE-09"])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert expected_key in finding.explanation
    assert "cite-checked" in finding.explanation


def test_cite_09_multi_citation_unmarked_keys(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Several methods exist~\\cite{smith2020, doe2021}.\n"
        "Partial check~\\citep{smith2020, doe2021}. % cite-checked: smith2020=SUPPORTED\n"
        "Two citations~\\cite{smith2020} and~\\cite{doe2021}. % cite-checked: smith2020=SUPPORTED\n",
        encoding="utf-8",
    )
    findings = check(root, rule_filter=["CITE-09"])
    assert len(findings) == 3

    # Line 1: both keys unmarked
    f1 = findings[0]
    assert f1.line == 1
    assert "smith2020" in f1.explanation
    assert "doe2021" in f1.explanation

    # Line 2: doe2021 unmarked
    f2 = findings[1]
    assert f2.line == 2
    assert "doe2021" in f2.explanation
    assert "smith2020" not in f2.explanation

    # Line 3: second \cite (doe2021) unmarked
    f3 = findings[2]
    assert f3.line == 3
    assert f3.column == 36
    assert "doe2021" in f3.explanation


@pytest.mark.parametrize(
    "source",
    [
        "This method is effective~\\cite{smith2020}. % cite-checked: SUPPORTED",
        "This method is effective~\\cite{smith2020}. % cite-checked: CONTRADICTED",
        "This method is effective~\\cite{smith2020}. % cite-checked: NOT_FOUND",
        "This method is effective~\\cite{smith2020}. % cite-checked: NUANCED",
        "Several algorithms exist~\\cite{smith2020, doe2021}. % cite-checked: SUPPORTED",
        "Several algorithms exist~\\cite{smith2020, doe2021}. % cite-checked: smith2020=SUPPORTED, doe2021=NOT_FOUND",
        "% This method is effective~\\cite{smith2020}.",
        "\\begin{verbatim}This method is effective~\\cite{smith2020}.\\end{verbatim}",
        "This method is effective~\\cite{smith2020}. % latex-lint: ignore=CITE-09",
        "Multiline citation~\\cite{\n  smith2020\n}. % cite-checked: SUPPORTED",
    ],
)
def test_cite_09_passing(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root, rule_filter=["CITE-09"])
    assert findings == []


def test_cite_09_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("Unchecked citation~\\cite{smith2020}.\n", encoding="utf-8")

    # Default check -> exit 0, no CITE-09 output
    assert cli_main(["check", str(root)]) == 0
    captured_default = capsys.readouterr()
    assert "CITE-09" not in captured_default.out

    # check --rule CITE-09 -> exit 1, reports CITE-09
    assert cli_main(["check", "--rule", "CITE-09", str(root)]) == 1
    captured_rule = capsys.readouterr()
    assert "CITE-09" in captured_rule.out
    assert "smith2020" in captured_rule.out

    # check --enable CITE-09 -> exit 1, reports CITE-09
    assert cli_main(["check", "--enable", "CITE-09", str(root)]) == 1
    captured_enable = capsys.readouterr()
    assert "CITE-09" in captured_enable.out

    # rule CITE-09 -> exit 0, documentation printed
    assert cli_main(["rule", "CITE-09"]) == 0
    captured_doc = capsys.readouterr()
    assert "CITE-09:" in captured_doc.out
    assert "Passing examples:" in captured_doc.out
