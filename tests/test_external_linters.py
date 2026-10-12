import shutil
import subprocess
from pathlib import Path

import pytest

from latex_linting.main import check


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("latex-lint")
    assert executable is not None, "uv must install the latex-lint console command"
    return subprocess.run([executable, *arguments], capture_output=True, text=True, check=False)  # noqa: S603 -- invoke CLI for test


has_chktex = shutil.which("chktex") is not None
has_lacheck = shutil.which("lacheck") is not None


@pytest.mark.skipif(not has_chktex, reason="chktex executable not found on PATH")
def test_chktex_detection_and_flag(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("See \\cite{ref1} for details.\n", encoding="utf-8")

    findings = check(root, chktex=True)
    chktex_findings = [f for f in findings if f.rule_id == "CHKTEX-2"]
    assert len(chktex_findings) == 1
    assert chktex_findings[0].filename == str(root)
    assert chktex_findings[0].line == 1

    disabled_findings = check(root, chktex=False)
    assert not any(f.rule_id.startswith("CHKTEX") for f in disabled_findings)

    cli_enabled = run_cli("check", str(root))
    assert cli_enabled.returncode == 1
    assert "CHKTEX-2" in cli_enabled.stdout

    cli_disabled = run_cli("check", "--no-chktex", str(root))
    assert "CHKTEX-2" not in cli_disabled.stdout


@pytest.mark.skipif(not has_lacheck, reason="lacheck executable not found on PATH")
def test_lacheck_detection_and_flag(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("\\begin{quote}\nUnclosed quote environment\n", encoding="utf-8")

    findings = check(root, lacheck=True)
    lacheck_findings = [f for f in findings if f.rule_id == "LACHECK"]
    assert len(lacheck_findings) >= 1
    assert lacheck_findings[0].filename == str(root)

    disabled_findings = check(root, lacheck=False)
    assert not any(f.rule_id == "LACHECK" for f in disabled_findings)

    cli_enabled = run_cli("check", str(root))
    assert cli_enabled.returncode == 1
    assert "LACHECK" in cli_enabled.stdout

    cli_disabled = run_cli("check", "--no-lacheck", str(root))
    assert "LACHECK" not in cli_disabled.stdout


@pytest.mark.skipif(not has_chktex, reason="chktex executable not found on PATH")
def test_chktex_suppression_in_source(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("See \\cite{ref1} for details. % latex-lint:ignore=CHKTEX-2\n", encoding="utf-8")

    findings = check(root, chktex=True)
    assert not any(f.rule_id == "CHKTEX-2" for f in findings)


@pytest.mark.skipif(not has_chktex, reason="chktex executable not found on PATH")
def test_chktex_suppression_generic_id(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("See \\cite{ref1} for details. % latex-lint:ignore=CHKTEX\n", encoding="utf-8")

    findings = check(root, chktex=True)
    assert not any(f.rule_id.startswith("CHKTEX") for f in findings)


@pytest.mark.skipif(not has_lacheck, reason="lacheck executable not found on PATH")
def test_lacheck_suppression_in_source(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("\\begin{quote} % latex-lint:ignore=LACHECK\nUnclosed quote environment\n", encoding="utf-8")

    findings = check(root, lacheck=True)
    assert not any(f.rule_id == "LACHECK" and f.line == 1 for f in findings)


@pytest.mark.skipif(not has_chktex, reason="chktex executable not found on PATH")
def test_chktex_cli_ignore(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text("See \\cite{ref1} for details.\n", encoding="utf-8")

    cli_result = run_cli("check", "--ignore", "CHKTEX-2", str(root))
    assert "CHKTEX-2" not in cli_result.stdout

    cli_generic = run_cli("check", "--ignore", "CHKTEX", str(root))
    assert "CHKTEX-2" not in cli_generic.stdout


@pytest.mark.skipif(not (has_chktex and has_lacheck), reason="linters not found on PATH")
def test_multi_file_external_linters(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    sub = tmp_path / "sub.tex"
    sub.write_text("See \\cite{ref1} for details.\n", encoding="utf-8")
    root.write_text("\\input{sub.tex}\n", encoding="utf-8")

    findings = check(root, chktex=True, lacheck=True)
    sub_chktex = [f for f in findings if f.rule_id == "CHKTEX-2"]
    assert len(sub_chktex) == 1
    assert sub_chktex[0].filename == str(sub)


def test_bib_file_skips_external(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text("@article{key,\n  title = {Title},\n}\n", encoding="utf-8")
    findings = check(bib, chktex=True, lacheck=True)
    assert not any(f.rule_id.startswith("CHKTEX") or f.rule_id == "LACHECK" for f in findings)


def test_missing_executable_warning(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "main.tex"
    root.write_text("Simple text\n", encoding="utf-8")

    monkeypatch.setattr(shutil, "which", lambda cmd: None if cmd in {"chktex", "lacheck"} else shutil.which(cmd))
    findings = check(root, chktex=True, lacheck=True)
    assert findings == []
    captured = capsys.readouterr()
    assert "latex-lint: warning: 'chktex' executable not found on PATH, skipping ChkTeX" in captured.err
    assert "latex-lint: warning: 'lacheck' executable not found on PATH, skipping LaCheck" in captured.err
