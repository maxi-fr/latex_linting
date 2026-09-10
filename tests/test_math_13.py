from pathlib import Path

from latex_linting.main import check


def test_valid_math_without_blank_lines(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_math_with_comment_only_line(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{align}\n  a &= b \\,,\n  % visual separator\n  c &= d \\,.\n\\end{align}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_math_with_bare_percent_comment_line(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  a = b \\,,\n  %\n  c = d \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_blank_line_inside_equation(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  a = b \\,,\n\n  c = d \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    math_13_findings = [f for f in findings if f.rule_id == "MATH-13"]
    assert len(math_13_findings) == 1
    assert math_13_findings[0].line == 3
    assert math_13_findings[0].column == 1


def test_whitespace_only_line_inside_align(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{align}\n  a &= b \\,,\n   \t  \n  c &= d \\,.\n\\end{align}\n",
        encoding="utf-8",
    )
    findings = check(root)
    math_13_findings = [f for f in findings if f.rule_id == "MATH-13"]
    assert len(math_13_findings) == 1
    assert math_13_findings[0].line == 3
    assert math_13_findings[0].column == 1


def test_blank_line_inside_bracket_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\[\n  a = b \\,,\n\n  c = d \\,.\n\\]\n",
        encoding="utf-8",
    )
    findings = check(root)
    math_13_findings = [f for f in findings if f.rule_id == "MATH-13"]
    assert len(math_13_findings) == 1
    assert math_13_findings[0].line == 3
    assert math_13_findings[0].column == 1


def test_multiple_blank_lines_reported(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  a = b \\,,\n\n\n  c = d \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    math_13_findings = [f for f in findings if f.rule_id == "MATH-13"]
    assert len(math_13_findings) == 2
    assert [f.line for f in math_13_findings] == [3, 4]


def test_disable_suppression_for_math_13(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% latex-lint:disable=MATH-13\n"
        "\\begin{equation}\n"
        "  a = b \\,,\n"
        "\n"
        "  c = d \\,.\n"
        "\\end{equation}\n"
        "% latex-lint:enable=MATH-13\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert not any(f.rule_id == "MATH-13" for f in findings)
