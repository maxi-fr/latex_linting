from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_struc_03_metadata() -> None:
    rule = get_rule("STRUC-03")
    assert rule.rule_id == "STRUC-03"
    assert "subheading" in rule.explanation.lower()
    assert "sibling" in rule.correction.lower() or "subheading" in rule.correction.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "reading order" in rule.limits


def test_isolated_section_under_chapter(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\chapter{Chapter One}\n\\section{Only Section}\n\\chapter{Chapter Two}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    finding = struc_03[0]
    assert finding.filename == str(root)
    assert (finding.line, finding.column) == (2, 1)
    assert finding.excerpt == "\\section{Only Section}"


def test_isolated_subsection_under_section(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\section{Section One}\n\\subsection{Only Subsection}\n\\section{Section Two}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    finding = struc_03[0]
    assert finding.filename == str(root)
    assert (finding.line, finding.column) == (2, 1)
    assert finding.excerpt == "\\subsection{Only Subsection}"


def test_two_children_satisfy_rule(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\chapter{Chapter One}\n"
        "\\section{Section 1.1}\n"
        "\\section{Section 1.2}\n"
        "\\chapter{Chapter Two}\n"
        "\\section{Section 2.1}\n"
        "\\subsection{Sub 2.1.1}\n"
        "\\subsection{Sub 2.1.2}\n"
        "\\section{Section 2.2}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-03"] == []


def test_zero_children_valid(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\chapter{Chapter One}\nProse only.\n\\chapter{Chapter Two}\nMore prose.\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-03"] == []


def test_adjacent_branches_not_confused(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\chapter{Chapter One}\n"
        "\\section{Section 1.1}\n"
        "\\subsection{Sub 1.1.1}\n"
        "\\subsection{Sub 1.1.2}\n"
        "\\section{Section 1.2}\n"
        "\\subsection{Sub 1.2.1}\n"
        "\\chapter{Chapter Two}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    assert (struc_03[0].line, struc_03[0].column) == (6, 1)
    assert struc_03[0].excerpt == "\\subsection{Sub 1.2.1}"


def test_starred_headings_do_not_count(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\chapter{Chapter One}\n\\section{Section 1.1}\n\\section*{Unnumbered Section}\n\\chapter{Chapter Two}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    assert (struc_03[0].line, struc_03[0].column) == (2, 1)


def test_comments_and_command_arguments_ignored(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\chapter{Chapter One}\n"
        "\\section{Only Section with \\texttt{\\section} in title}\n"
        "% \\section{Commented Out Section}\n"
        "\\chapter{Chapter Two}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    assert struc_03[0].line == 2


def test_same_line_ignore_suppresses_struc_03(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\chapter{Chapter One}\n\\section{Only Section} % latex-lint:ignore=STRUC-03\n\\chapter{Chapter Two}\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-03"] == []
