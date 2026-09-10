from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_section_ending_on_prose(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n"
        "\\begin{equation}\n"
        "  E = mc^2 \\,.\n"
        "\\end{equation}\n"
        "This relation governs our model.\n"
        "\\section{Results}\n"
        "We discuss our results here.\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_section_ending_on_equation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n"
        "\\begin{equation}\n"
        "  E = mc^2 \\,.\n"
        "\\end{equation}\n"
        "\\section{Results}\n"
        "We discuss our results here.\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].line == 4
    assert struc_06[0].column == 1


def test_section_ending_on_bracket_math(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n\\[\n  E = mc^2 \\,.\n\\]\n\\section{Results}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].line == 4
    assert struc_06[0].column == 1


@pytest.mark.parametrize(
    "env",
    [
        "itemize",
        "enumerate",
        "description",
        "figure",
        "table",
        "tabular",
    ],
)
def test_section_ending_on_non_prose_blocks(tmp_path: Path, env: str) -> None:
    root = tmp_path / "thesis.tex"
    if env in {"itemize", "enumerate", "description"}:
        body = "\\item Item A\n"
    elif env == "tabular":
        body = "{c}\n1 \\\\\n"
    else:
        body = "\\caption{Test caption.}\n"
    root.write_text(
        f"\\section{{Section A}}\n\\begin{{{env}}}\n{body}\\end{{{env}}}\n\\section{{Section B}}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1


def test_section_ending_before_document_end(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{document}\n"
        "\\section{Final Section}\n"
        "\\begin{equation}\n"
        "  E = mc^2 \\,.\n"
        "\\end{equation}\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].line == 5


def test_section_ending_before_eof(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Final Section}\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].line == 4


def test_trailing_label_and_comment_do_not_count_as_prose(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n"
        "\\begin{equation}\n"
        "  E = mc^2 \\,.\n"
        "\\end{equation}\n"
        "\\label{eq:last}\n"
        "% trailing comment\n"
        "\\clearpage\n"
        "\\section{Results}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].line == 4


def test_prose_continuation_in_included_file_satisfies_rule(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    part1 = tmp_path / "part1.tex"
    part2 = tmp_path / "part2.tex"
    root.write_text(
        "\\section{Methods}\n\\input{part1.tex}\n\\input{part2.tex}\n\\section{Results}\n",
        encoding="utf-8",
    )
    part1.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    part2.write_text(
        "This prose continuation follows the equation.\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_violation_in_included_file_reported_in_included_file(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    part1 = tmp_path / "part1.tex"
    root.write_text(
        "\\section{Methods}\n\\input{part1.tex}\n\\section{Results}\n",
        encoding="utf-8",
    )
    part1.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    struc_06 = [f for f in findings if f.rule_id == "STRUC-06"]
    assert len(struc_06) == 1
    assert struc_06[0].filename == str(part1)
    assert struc_06[0].line == 3


def test_same_line_ignore_suppression_for_struc_06(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n"
        "\\begin{equation}\n"
        "  E = mc^2 \\,.\n"
        "\\end{equation} % latex-lint:ignore=STRUC-06\n"
        "\\section{Results}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert not any(f.rule_id == "STRUC-06" for f in findings)
