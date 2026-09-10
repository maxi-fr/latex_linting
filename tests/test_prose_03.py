from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_prose_03_metadata() -> None:
    rule = get_rule("PROSE-03")
    assert rule.rule_id == "PROSE-03"
    assert "Suspected comma-before-that" in rule.explanation
    assert "restrictive" in rule.explanation
    assert "parenthetical" in rule.explanation
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "ambiguity" in rule.limits.lower() or "restrictive" in rule.limits.lower()


@pytest.mark.parametrize(
    ("text", "expected_col"),
    [
        ("We note, that this approach is effective.", 8),
        ("It is clear, that the algorithm converges.", 12),
        ("The hypothesis, that the model improves, was tested.", 15),
    ],
)
def test_prose_03_violations(text: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(text + "\n", encoding="utf-8")
    findings = check(root)
    prose_03 = [f for f in findings if f.rule_id == "PROSE-03"]
    assert len(prose_03) >= 1
    finding = prose_03[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert "Suspected comma-before-that" in finding.explanation
    assert "comma" in finding.correction


@pytest.mark.parametrize(
    "source",
    [
        "We note that this approach is effective.",
        "It is clear that the algorithm converges.",
        "The hypothesis that the model improves was tested.",
        "% We note, that this is in a comment.",
        "\\begin{verbatim}data, that = load()\\end{verbatim}",
        "\\verb|value, that|",
        "$x, that \\in S$",
        "\\cite{smith2020, that2021}",
        "\\label{sec:first, that}",
    ],
)
def test_prose_03_valid_counterparts(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-03"] == []


def test_prose_03_multiline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "We note,\nthat this is on another line.\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_03 = [f for f in findings if f.rule_id == "PROSE-03"]
    assert len(prose_03) == 1
    assert (prose_03[0].line, prose_03[0].column) == (1, 8)


def test_prose_03_nested_in_prose_command(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\emph{We note, that it works.}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_03 = [f for f in findings if f.rule_id == "PROSE-03"]
    assert len(prose_03) == 1
    assert (prose_03[0].line, prose_03[0].column) == (1, 14)


def test_prose_03_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "We note, that this idiom is kept. % latex-lint:ignore=PROSE-03\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-03"] == []


def test_prose_03_german_passage_disabled(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "% latex-lint:disable=PROSE-03\n"
        "Wir stellen fest, that is in German.\n"
        "% latex-lint:enable=PROSE-03\n"
        "Now in English, that violates.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_03 = [f for f in findings if f.rule_id == "PROSE-03"]
    assert len(prose_03) == 1
    assert prose_03[0].line == 4
