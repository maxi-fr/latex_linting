from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_struc_02_metadata() -> None:
    rule = get_rule("STRUC-02")
    assert rule.rule_id == "STRUC-02"
    assert "three" in rule.explanation
    assert "unnumbered" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "secnumdepth" in rule.limits


@pytest.mark.parametrize(
    ("heading_code", "expected_col"),
    [
        (r"\subsubsection{Too Deep}", 1),
        (r"  \paragraph{Too Deep}", 3),
        (r"\subparagraph{Too Deep}", 1),
        (r"\subsubsection[Short Title]{Long Title}", 1),
    ],
)
def test_struc_02_violations(heading_code: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(f"Text before\n{heading_code}\nText after\n", encoding="utf-8")
    findings = check(root)
    struc_02 = [f for f in findings if f.rule_id == "STRUC-02"]
    assert len(struc_02) == 1
    finding = struc_02[0]
    assert finding.filename == str(root)
    assert finding.line == 2
    assert finding.column == expected_col
    assert "three" in finding.explanation
    assert "unnumbered" in finding.correction


@pytest.mark.parametrize(
    "source",
    [
        r"\chapter{Valid Level}",
        r"\section{Valid Level}",
        r"\subsection{Valid Level}",
        r"\subsubsection*{Unnumbered Subsubsection}",
        r"\paragraph*{Unnumbered Paragraph}",
        r"\subparagraph*{Unnumbered Subparagraph}",
        r"\subsubsection*[Short Title]{Unnumbered Subsubsection}",
        r"% \subsubsection{Commented Out}",
        r"\begin{verbatim}\subsubsection{In code}\end{verbatim}",
        r"\begin{lstlisting}\paragraph{In code}\end{lstlisting}",
    ],
)
def test_struc_02_valid_counterparts(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-02"] == []


def test_struc_02_multiline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\subsubsection[\n  Short\n]{\n  Long Title\n}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_02 = [f for f in findings if f.rule_id == "STRUC-02"]
    assert len(struc_02) == 1
    assert (struc_02[0].line, struc_02[0].column) == (1, 1)


def test_struc_02_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"\subsubsection{Too Deep} % latex-lint:ignore=STRUC-02" + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-02"] == []
