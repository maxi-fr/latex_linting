from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_prose_04_metadata() -> None:
    rule = get_rule("PROSE-04")
    assert rule.rule_id == "PROSE-04"
    assert "American headline" in rule.explanation
    assert "Capitalize" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "acronym" in rule.limits.lower()
    assert "hyphen" in rule.limits.lower()
    assert "math" in rule.limits.lower()


@pytest.mark.parametrize(
    ("heading_code", "expected_col"),
    [
        (r"\section{Methods in machine learning}", 1),
        (r"\section{methods and Tools}", 1),
        (r"\section{Methods and tools}", 1),
        (r"\section{Methods In Machine Learning}", 1),
        (r"\section{Methods Of Analysis}", 1),
        (r"\chapter{An introduction to robotics}", 1),
        (r"\subsection{What the System is}", 1),
        (r"\section{Closed-loop Systems}", 1),
        (r"  \section{Methods and tools}", 3),
        (r"\subsubsection{A Study on neural Networks}", 1),
    ],
)
def test_prose_04_violations(heading_code: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(heading_code + "\n", encoding="utf-8")
    findings = check(root)
    prose_04 = [f for f in findings if f.rule_id == "PROSE-04"]
    assert len(prose_04) == 1
    finding = prose_04[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert "American headline" in finding.explanation
    assert "Capitalize" in finding.correction


@pytest.mark.parametrize(
    "source",
    [
        r"\chapter{A Really Awesome Thesis}",
        r"\section{Closed-Loop Deep Brain Stimulation}",
        r"\section{State-of-the-Art Methods}",
        r"\section{Methods and Tools}",
        r"\section{A Study on Neural Networks}",
        r"\section{What the System Is}",
        r"\section{Overview of API and CNN Architectures}",
        r"\section{Optimization of $H_\infty$ Controllers}",
        r"\section{Overview of \emph{Deep} Learning}",
        r"\section*{Unnumbered Heading Example}",
        r"\section[Short Title]{Long Title in Heading Case}",
        r"% \section{methods in machine learning}",
        r"\begin{verbatim}\section{methods in machine learning}\end{verbatim}",
        r"\verb|\section{methods in machine learning}|",
    ],
)
def test_prose_04_valid_counterparts(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-04"] == []


def test_prose_04_multiline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\section{\n  Methods in\n  machine learning\n}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_04 = [f for f in findings if f.rule_id == "PROSE-04"]
    assert len(prose_04) == 1
    assert (prose_04[0].line, prose_04[0].column) == (1, 1)


def test_prose_04_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\section{methods in machine learning} % latex-lint:ignore=PROSE-04\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-04"] == []
