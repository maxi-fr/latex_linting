from pathlib import Path

from latex_linting.main import check


def test_hierarchy_across_includes_satisfies_rule(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"

    root.write_text(
        "\\chapter{First Chapter}\n\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text("\\section{First Section}\nProse here.\n", encoding="utf-8")
    ch2.write_text("\\section{Second Section}\nMore prose.\n", encoding="utf-8")

    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-03"] == []


def test_isolated_subheading_in_included_file_reported_with_actionable_location(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"

    root.write_text(
        "\\chapter{First Chapter}\n\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "\\section{First Section}\n\\subsection{Only Subsection}\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "\\section{Second Section}\n\\subsection{Sub A}\n\\subsection{Sub B}\n",
        encoding="utf-8",
    )

    findings = check(root)
    struc_03 = [f for f in findings if f.rule_id == "STRUC-03"]
    assert len(struc_03) == 1
    finding = struc_03[0]
    assert finding.filename == str(ch1)
    assert finding.line == 2
    assert finding.column == 1
    assert finding.excerpt == "\\subsection{Only Subsection}"


def test_isolated_subheading_in_included_file_suppressed_by_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"

    root.write_text(
        "\\chapter{First Chapter}\n\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "\\section{First Section}\n\\subsection{Only Subsection} % latex-lint:ignore=STRUC-03\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "\\section{Second Section}\n\\subsection{Sub A}\n\\subsection{Sub B}\n",
        encoding="utf-8",
    )

    findings = check(root)
    assert [f for f in findings if f.rule_id == "STRUC-03"] == []
