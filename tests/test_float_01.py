from pathlib import Path

import pytest

from latex_linting.cli import main as cli_main
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule
from latex_linting.rules.float_01 import RULE


def test_rule_metadata() -> None:
    """Verify FLOAT-01 rule metadata, default enabled state, and warning severity."""
    assert RULE.rule_id == "FLOAT-01"
    assert RULE.severity == "warning"
    assert RULE.enabled_by_default is True
    assert get_rule("FLOAT-01") is RULE


@pytest.mark.parametrize(
    ("env", "arg"),
    [
        ("figure", "[!tb]"),
        ("figure", "[htp]"),
        ("figure", "[h!]"),
        ("figure", "[H]"),
        ("figure*", "[!t]"),
        ("table", "[htbp]"),
        ("table", "[h]"),
        ("table*", "[t]"),
    ],
)
def test_float_with_optional_placement_flagged(env: str, arg: str, tmp_path: Path) -> None:
    """Flag float environments with optional placement arguments as warnings."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        f"\\begin{{{env}}}{arg}\n"
        "  \\centering\n"
        "  \\caption{Caption text.}\\label{fig:test}\n"
        f"\\end{{{env}}}\n"
        "Figure~\\ref{fig:test} describes the concept.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FLOAT-01"]
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "FLOAT-01"
    assert finding.severity == "warning"
    assert finding.line == 1
    assert arg in finding.explanation
    assert arg in finding.correction


def test_float_without_optional_placement_passes(tmp_path: Path) -> None:
    """Pass float environments without optional placement arguments."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\includegraphics{pic.png}\n"
        "  \\caption{Caption text.}\\label{fig:pic}\n"
        "\\end{figure}\n"
        "\\begin{table}\n"
        "  \\centering\n"
        "  \\caption{Table caption.}\\label{tab:data}\n"
        "  \\begin{tabular}{ll}\\toprule A & B \\\\\\bottomrule\\end{tabular}\n"
        "\\end{table}\n"
        "Figure~\\ref{fig:pic} and Table~\\ref{tab:data} are valid.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FLOAT-01"]
    assert findings == []


def test_float_whitespace_and_comment_variations(tmp_path: Path) -> None:
    """Detect optional bracket argument even when separated by spaces or comments."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}   [!tb]\n"
        "  \\centering\n"
        "  \\caption{Spaced figure.}\\label{fig:spaced}\n"
        "\\end{figure}\n"
        "\\begin{table}% comment before placement\n"
        "  [ht]\n"
        "  \\centering\n"
        "  \\caption{Commented table.}\\label{tab:comment}\n"
        "  \\begin{tabular}{l}\\toprule A\\\\\\bottomrule\\end{tabular}\n"
        "\\end{table}\n"
        "Figure~\\ref{fig:spaced} and Table~\\ref{tab:comment}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FLOAT-01"]
    assert len(findings) == 2
    assert findings[0].line == 1
    assert findings[1].line == 6


def test_float_placement_suppression(tmp_path: Path) -> None:
    """Suppress FLOAT-01 warning with inline comment directive."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}[!tb] % latex-lint:ignore=FLOAT-01\n"
        "  \\centering\n"
        "  \\caption{Suppressed figure.}\\label{fig:supp}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:supp}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FLOAT-01"]
    assert findings == []


def test_cli_warning_exit_code_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit code is 0 when only FLOAT-01 warning is present."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}[!tb]\n"
        "  \\centering\n"
        "  \\caption{Figure with manual placement.}\\label{fig:warn}\n"
        "\\end{figure}\n"
        "Figure~\\ref{fig:warn} is floating.\n",
        encoding="utf-8",
    )
    code = cli_main(["check", str(root)])
    assert code == 0
    captured = capsys.readouterr()
    assert "[warning]" in captured.out
    assert "FLOAT-01 [warning]" in captured.out


def test_float_unclosed_bracket_ignored(tmp_path: Path) -> None:
    """Ignore unclosed bracket following float environment."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}[ht\n"
        "  \\centering\n"
        "  \\caption{Unclosed bracket figure.}\\label{fig:unclosed}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "FLOAT-01"]
    assert findings == []
