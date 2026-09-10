from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_cite_04_metadata() -> None:
    rule = get_rule("CITE-04")
    assert rule.rule_id == "CITE-04"
    assert "terminal period" in rule.explanation
    assert "before" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "optional argument" in rule.limits.lower() or "arguments" in rule.limits.lower()
    assert "et al." in rule.limits


@pytest.mark.parametrize(
    ("text", "expected_col"),
    [
        ("This method is effective. \\cite{smith2020}", 27),
        ("This method is effective.\\cite{smith2020}", 26),
        ("This method is effective.~\\cite{smith2020}", 27),
        ("This method is effective. \\citep[p.~5]{smith2020}", 27),
        ("This method is effective. \\citet[see][p.~10]{smith2020}", 27),
        ("This method is effective. \\autocite{smith2020}", 27),
        ("This method is effective. \\parencite{smith2020}", 27),
        ("This method is effective. \\footcite{smith2020}", 27),
        ("This method is effective. \\textcite{smith2020}", 27),
    ],
)
def test_cite_04_violations(text: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(text + "\n", encoding="utf-8")
    findings = check(root)
    cite_04 = [f for f in findings if f.rule_id == "CITE-04"]
    assert len(cite_04) == 1
    finding = cite_04[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert "terminal period" in finding.explanation
    assert "before" in finding.correction


@pytest.mark.parametrize(
    "source",
    [
        "This method is effective~\\cite{smith2020}.",
        "This method is effective~\\citep[p.~5]{smith2020}.",
        "This method is effective~\\autocite{smith2020}.",
        "According to \\citet{smith2020}, this approach is superior.",
        "As shown by Smith et al.~\\cite{smith2020}.",
        "As shown by Smith et al. \\cite{smith2020}.",
        "% This method is effective. \\cite{smith2020}",
        "\\begin{verbatim}This method is effective. \\cite{smith2020}\\end{verbatim}",
        "\\verb|text. \\cite{ref}|",
        "$x = 1. \\cite{foo}$",
    ],
)
def test_cite_04_valid_counterparts(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "CITE-04"] == []


def test_cite_04_multiline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "This method is effective.\n  \\cite{smith2020}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    cite_04 = [f for f in findings if f.rule_id == "CITE-04"]
    assert len(cite_04) == 1
    assert (cite_04[0].line, cite_04[0].column) == (2, 3)


def test_cite_04_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "This is effective. \\cite{smith2020} % latex-lint:ignore=CITE-04\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "CITE-04"] == []
