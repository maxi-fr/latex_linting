import shutil
import subprocess
from pathlib import Path

import pytest

from latex_linting.main import check


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("latex-lint")
    assert executable is not None, "uv must install the latex-lint console command"
    return subprocess.run([executable, *arguments], capture_output=True, text=True, check=False)  # noqa: S603 -- invoke the installed command with test arguments


def test_clean_check(tmp_path: Path) -> None:
    root = tmp_path / "clean.tex"
    root.write_text(r"$a/b$", encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_findings_match_library(tmp_path: Path) -> None:
    root = tmp_path / "bad.tex"
    root.write_text("Text\n$\\frac{a}{b} + \\frac{c}{d}$", encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 1
    assert result.stderr == ""
    for finding in check(root):
        assert f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id}" in result.stdout
        assert finding.explanation in result.stdout
        assert finding.excerpt in result.stdout
        assert finding.correction in result.stdout


@pytest.mark.parametrize("arguments", [("check",), ("check", "missing.tex"), ("rule", "UNKNOWN"), ()])
def test_invalid_arguments(arguments: tuple[str, ...]) -> None:
    result = run_cli(*arguments)
    assert result.returncode == 2
    assert result.stderr
    assert "Traceback" not in result.stderr


def test_invalid_encoding(tmp_path: Path) -> None:
    root = tmp_path / "invalid.tex"
    root.write_bytes(b"\xff")
    result = run_cli("check", str(root))
    assert result.returncode == 2
    assert result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "rule_id",
    [
        "CITE-04",
        "MATH-01",
        "MATH-04",
        "MATH-13",
        "PROSE-02",
        "PROSE-03",
        "PROSE-04",
        "PROSE-07",
        "STRUC-02",
        "STRUC-03",
        "STRUC-06",
        "WORK-03",
    ],
)
def test_rule_help(rule_id: str) -> None:
    result = run_cli("rule", rule_id)
    assert result.returncode == 0
    assert rule_id in result.stdout
    assert "Passing examples" in result.stdout
    assert "Failing examples" in result.stdout
    assert "Detection limits" in result.stdout


def test_cli_ticket_05_rules_reporting(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{methods in machine learning}\n"
        "This is a standalone demonstrative.\n"
        "We note, that the comma is present.\n"
        "The method is effective. \\cite{smith2020}\n"
    )
    root.write_text(source, encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 1
    for finding in check(root):
        assert f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id}" in result.stdout
        assert finding.explanation in result.stdout
        assert finding.excerpt in result.stdout
        assert finding.correction in result.stdout


def test_cli_ticket_06_rules_reporting(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{Methods in Machine Learning}\n"
        "The relation is:\n"
        "\\begin{equation}\n"
        "\n"
        "  E = mc^2\n"
        "\\end{equation}\n"
        "\\section{Results and Discussion}\n"
        "We discuss results here.\n"
    )
    root.write_text(source, encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 1
    api_findings = check(root)
    rule_ids = {f.rule_id for f in api_findings}
    assert rule_ids == {"PROSE-07", "MATH-13", "MATH-01", "STRUC-06"}
    for finding in api_findings:
        assert f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id}" in result.stdout
        assert finding.explanation in result.stdout
        assert finding.excerpt in result.stdout
        assert finding.correction in result.stdout


def test_cli_suppressed_violation_passes(tmp_path: Path) -> None:
    bad = tmp_path / "bad.tex"
    bad.write_text(r"$\frac{a}{b}$", encoding="utf-8")
    assert run_cli("check", str(bad)).returncode == 1

    suppressed = tmp_path / "suppressed.tex"
    suppressed.write_text(r"$\frac{a}{b}$ % latex-lint:ignore=MATH-04", encoding="utf-8")
    result = run_cli("check", str(suppressed))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_cli_ignore_option(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$\frac{a}{b}$", encoding="utf-8")
    assert run_cli("check", "--ignore", "MATH-04", str(root)).returncode == 0
    assert run_cli("check", str(root), "--ignore", "MATH-04").returncode == 0
    assert run_cli("check", "--ignore", " MATH-04, MATH-04 ", str(root)).returncode == 0


def test_cli_unknown_rule_in_ignore_option(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(r"$a/b$", encoding="utf-8")
    result = run_cli("check", "--ignore", "UNKNOWN", str(root))
    assert result.returncode == 2
    assert "UNKNOWN" in result.stderr
    assert "Traceback" not in result.stderr
    assert run_cli("check", "--ignore", "MATH-04, ", str(root)).returncode == 2


def test_cli_unknown_rule_in_source_directive(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("% latex-lint:ignore=UNKNOWN\n$a/b$\n", encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 2
    assert "UNKNOWN" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_multi_file_thesis(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    inc = tmp_path / "inc.tex"
    root.write_text("$\\frac{1}{2}$\n\\input{inc.tex}\n", encoding="utf-8")
    inc.write_text("$\\frac{3}{4}$\n", encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 1
    assert result.stderr == ""
    api_findings = check(root)
    assert len(api_findings) == 2
    for finding in api_findings:
        assert f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id}" in result.stdout
        assert finding.excerpt in result.stdout
        assert finding.correction in result.stdout


def test_cli_missing_included_file(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("Intro\n\\input{missing.tex}\n", encoding="utf-8")
    result = run_cli("check", str(root))
    assert result.returncode == 2
    assert "missing.tex" in result.stderr
    assert "2" in result.stderr
    assert "Traceback" not in result.stderr
