from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_decimal_period(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$3.14$ and $0.05$ and $100.25$ and $2.718$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []


def test_valid_decimal_comma_in_braces(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$3{,}14$ and $0{,}05$ and $2{,}718$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []


def test_valid_comma_separated_list_with_space(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$(1, 2)$ and $f(x, y)$ and $(3, 14)$ and $\\{1, 2, 3\\}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []


@pytest.mark.parametrize(
    ("expr", "comma_col"),
    [
        ("$3,14$", 3),
        ("$0,05$", 3),
        ("$100,25$", 5),
        ("$(1,2)$", 4),
    ],
)
def test_decimal_comma_violations(tmp_path: Path, expr: str, comma_col: int) -> None:
    root = tmp_path / "math.tex"
    root.write_text(f"{expr}\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "MATH-14"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-14"
    assert findings[0].line == 1
    assert findings[0].column == comma_col
    assert "English" in findings[0].explanation


def test_decimal_comma_in_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  x = 2,718 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-14"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-14"
    assert findings[0].line == 2
    assert findings[0].column == 8


def test_math_14_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$3,14$ % latex-lint:ignore=MATH-14\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []


def test_math_14_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% latex-lint:disable=MATH-14\n$3,14$\n% latex-lint:enable=MATH-14\n$3,14$\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-14"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_math_14_invocation_ignore(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text("$3,14$\n", encoding="utf-8")
    findings = check(root, ignored_rules=["MATH-14"])
    assert [f for f in findings if f.rule_id == "MATH-14"] == []


def test_math_14_context_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% $3,14$\n\\begin{verbatim}\n$3,14$\n\\end{verbatim}\n$\\text{see section 3,14 for details}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []


def test_valid_multi_index_subscripts_and_superscripts(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$x_{1,1}$ and $x_{i,1}$ and $x_{1,2,3}$ and $A^{1,2}$ and $y_{1,1}^{(k)}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-14"] == []
