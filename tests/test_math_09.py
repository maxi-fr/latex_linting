from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_math_operators(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$a \\cdot b$ and $x \\neq y$ and $x = y$ and $a \\land b$ and $a \\lor b$ and $x \\le y$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-09"] == []


def test_valid_latex_commands_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$\\alpha + \\beta + \\frac{a}{b} + \\sum_{i=1}^n x_i + \\int f(x)\\,\\mathrm{d}x$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-09"] == []


def test_valid_superscripts_and_subscripts_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$x^*$ and $A^*$ and $x^{*}$ and $x_*$ and $x_{*}$ and $f^*(y)$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-09"] == []


@pytest.mark.parametrize(
    ("expr", "op_col"),
    [
        ("$a * b$", 4),
        ("$2 * 3$", 4),
        ("$x * y$", 4),
        ("$2*x$", 3),
        ("$x != y$", 4),
        ("$x ~= y$", 4),
        ("$x == y$", 4),
        ("$a && b$", 4),
        ("$a || b$", 4),
        ("$x <= y$", 4),
        ("$x >= y$", 4),
        ("$A .* B$", 4),
        ("$A .^ 2$", 4),
        ("$A ./ B$", 4),
        ("$x ** 2$", 4),
    ],
)
def test_programming_operator_violations(tmp_path: Path, expr: str, op_col: int) -> None:
    root = tmp_path / "math.tex"
    root.write_text(f"{expr}\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "MATH-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-09"
    assert findings[0].line == 1
    assert findings[0].column == op_col


def test_programming_operator_in_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  y = a * x + b \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-09"
    assert findings[0].line == 2
    assert findings[0].column == 9


def test_math_09_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$a * b$ % latex-lint:ignore=MATH-09\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-09"] == []


def test_math_09_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% latex-lint:disable=MATH-09\n$a * b$\n% latex-lint:enable=MATH-09\n$a * b$\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-09"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_math_09_invocation_ignore(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text("$a * b$\n", encoding="utf-8")
    findings = check(root, ignored_rules=["MATH-09"])
    assert [f for f in findings if f.rule_id == "MATH-09"] == []


def test_math_09_context_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% $a * b$\n\\begin{verbatim}\n$a * b$\n\\end{verbatim}\n$\\text{code uses * and != operators}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-09"] == []
