from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_number_unit_thin_space(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$10\\,\\mathrm{kg}$ and $10\\,\\text{m}$ and $10\\,kg$ and $10\\,\\mathrm{m}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []


def test_valid_siunitx_commands(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$\\SI{10}{kg}$ and $\\qty{10}{\\meter}$ and $\\unit{kg}$ and $\\si{m/s}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []


def test_valid_algebraic_products_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$2x + 3a + 4y$ and $10m$ and $5s$ and $2 x$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []


def test_valid_display_math_with_thin_space(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  F = 100\\,\\mathrm{N} \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []


@pytest.mark.parametrize(
    "snippet",
    [
        "$10\\mathrm{kg}$",
        "$10 \\mathrm{kg}$",
        "$10~\\mathrm{kg}$",
        "$10\\text{m}$",
        "$10 \\text{m}$",
        "$10\\mathrm{m}$",
        "$10 \\mathrm{m}$",
        "$10kg$",
        "$10 kg$",
        "$10~kg$",
        "$5Hz$",
        "$5 Hz$",
        "$50kHz$",
        "$50 kHz$",
        "$2.4GHz$",
        "$2.4 GHz$",
        "$10mm$",
        "$10 mm$",
        "$5cm$",
        "$5 cm$",
        "$100km$",
        "$100 km$",
        "$12mV$",
        "$12 mV$",
        "$5mA$",
        "$5 mA$",
        "$10kW$",
        "$10 kW$",
        "$2MW$",
        "$2 MW$",
        "$20ms$",
        "$20 ms$",
        "$45deg$",
        "$45 deg$",
        "$3.14rad$",
        "$3.14 rad$",
        "$60dB$",
        "$60 dB$",
    ],
)
def test_number_unit_spacing_violations(tmp_path: Path, snippet: str) -> None:
    root = tmp_path / "math.tex"
    root.write_text(f"{snippet}\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "MATH-06"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-06"
    assert findings[0].line == 1
    assert findings[0].column == 2


def test_number_unit_spacing_in_display_math(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "\\begin{equation}\n  m = 5 kg \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-06"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-06"
    assert findings[0].line == 2
    assert findings[0].column == 7


def test_math_06_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "$10 kg$ % latex-lint:ignore=MATH-06\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []


def test_math_06_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% latex-lint:disable=MATH-06\n$10 kg$\n% latex-lint:enable=MATH-06\n$10 kg$\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-06"]
    assert len(findings) == 1
    assert findings[0].line == 4


def test_math_06_invocation_ignore(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text("$10 kg$\n", encoding="utf-8")
    findings = check(root, ignored_rules=["MATH-06"])
    assert [f for f in findings if f.rule_id == "MATH-06"] == []


def test_math_06_context_boundaries(tmp_path: Path) -> None:
    root = tmp_path / "math.tex"
    root.write_text(
        "% $10 kg$\n\\begin{verbatim}\n$10 kg$\n\\end{verbatim}\n$\\text{the weight is 10 kg}$\n",
        encoding="utf-8",
    )
    assert [f for f in check(root) if f.rule_id == "MATH-06"] == []
