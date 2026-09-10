from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_equation_terminal_period(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_equation_terminal_comma(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  a = b \\,,\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_bracket_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\[\n  x = y \\,.\n\\]\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_double_dollar_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$$\n  x = y \\,.\n$$\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_with_trailing_label_and_comment(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,. % Mass-energy equivalence\n  \\label{eq:einstein}\n\\end{equation}\n"
        "See~\\eqref{eq:einstein}.\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_multiline_align(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{align}\n  a &= b \\\\\n  c &= d \\,.\n\\end{align}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_multiline_align_with_trailing_linebreak(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{align}\n  a &= b \\\\\n  c &= d \\,. \\\\\n\\end{align}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_nested_environment_with_punctuation_outside(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  A = \\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix} \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


@pytest.mark.parametrize(
    "env",
    [
        "equation",
        "equation*",
        "align",
        "align*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "alignat",
        "alignat*",
        "flalign",
        "flalign*",
        "eqnarray",
        "eqnarray*",
    ],
)
def test_missing_punctuation_all_environments(tmp_path: Path, env: str) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        f"\\begin{{{env}}}\n  E = mc^2\n\\end{{{env}}}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"
    assert findings[0].line == 3
    assert findings[0].column == 1


def test_punctuation_without_thin_space(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"
    assert findings[0].line == 3
    assert findings[0].column == 1


def test_wrong_spacing_before_punctuation(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2\\;.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"


def test_period_inside_nested_matrix_does_not_count_as_terminal(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  A = \\begin{pmatrix} 1.5 & 2 \\end{pmatrix}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"


def test_period_in_trailing_label_does_not_count_as_terminal(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2\n  \\label{eq:sec1.1}\n\\end{equation}\nSee~\\eqref{eq:sec1.1}.\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"
    assert findings[0].line == 4


def test_period_in_trailing_comment_does_not_count_as_terminal(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 % This ends with a period.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"


def test_same_line_suppression_on_closing_delimiter(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2\n\\end{equation} % latex-lint:ignore=MATH-01\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_bracket_math_missing_punctuation(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\[\n  x = y\n\\]\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-01"
    assert findings[0].line == 3
    assert findings[0].column == 1


def test_bracket_math_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text("\\[ x = y \\] % latex-lint:ignore=MATH-01\n", encoding="utf-8")
    assert check(root) == []
