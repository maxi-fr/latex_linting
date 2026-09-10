from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_upright_standard_functions(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$\\sin(x)$ and $\\cos(\\theta)$ and $\\exp(-t)$ and $\\ln(x)$ and $\\log(x)$ and $\\min(a, b)$ and $\\max(a, b)$\n"
        "and $\\sup(S)$ and $\\inf(S)$ and $\\lim_{x \\to 0} f(x)$ and $\\det(A)$ and $\\arg(z)$ and $\\deg(P)$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []


def test_valid_constants_and_single_letters_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$e^{i\\pi} + 1 = 0$ and $E = mc^2$ and $j = \\sqrt{-1}$ and $d x$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []


def test_valid_upright_command_arguments(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$\\mathrm{sin}$ and $\\operatorname{sin}(x)$ and $\\mathbf{sin}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []


@pytest.mark.parametrize(
    ("expr", "func_col", "func_name"),
    [
        ("$sin(x)$", 2, "sin"),
        ("$cos(\\theta)$", 2, "cos"),
        ("$tan(x)$", 2, "tan"),
        ("$exp(-t)$", 2, "exp"),
        ("$ln(x)$", 2, "ln"),
        ("$log(x)$", 2, "log"),
        ("$min(a, b)$", 2, "min"),
        ("$max(a, b)$", 2, "max"),
        ("$sup(S)$", 2, "sup"),
        ("$inf(S)$", 2, "inf"),
        ("$lim_{x \\to 0}$", 2, "lim"),
        ("$det(A)$", 2, "det"),
        ("$arg(z)$", 2, "arg"),
        ("$deg(P)$", 2, "deg"),
    ],
)
def test_standard_function_notation_violations(tmp_path: Path, expr: str, func_col: int, func_name: str) -> None:
    root = tmp_path / "math.tex"
    root.write_text(f"{expr}\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "MATH-12"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-12"
    assert findings[0].line == 1
    assert findings[0].column == func_col
    assert f"\\{func_name}" in findings[0].correction


def test_word_boundaries_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$using + cosine + single$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []


def test_standard_function_in_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  y = sin(x) \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-12"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-12"
    assert findings[0].line == 2
    assert findings[0].column == 7


def test_math_12_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$sin(x)$ % latex-lint:ignore=MATH-12\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []


def test_math_12_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% latex-lint:disable=MATH-12\n$sin(x)$\n% latex-lint:enable=MATH-12\n$sin(x)$\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-12"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_math_12_invocation_ignore(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text("$sin(x)$\n", encoding="utf-8")
    findings = check(root, ignored_rules=["MATH-12"])
    assert [f for f in findings if f.rule_id == "MATH-12"] == []


def test_math_12_context_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% $sin(x)$\n\\begin{verbatim}\n$sin(x)$\n\\end{verbatim}\n$\\text{the sin curve is smooth}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-12"] == []
