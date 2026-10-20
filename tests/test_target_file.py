import shutil
import subprocess
from pathlib import Path

from latex_linting.main import check


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("latex-lint")
    assert executable is not None, "uv must install the latex-lint console command"
    return subprocess.run([executable, *arguments], capture_output=True, text=True, check=False)  # noqa: S603 -- invoke the installed command with test arguments


def test_root_document_reports_all_findings(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "$\\frac{1}{2}$\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 2
    filenames = [f.filename for f in findings]
    assert str(root) in filenames
    assert str(sub) in filenames


def test_subfile_reports_only_its_findings(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "$\\frac{1}{2}$\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    findings = check(sub)
    assert len(findings) == 1
    assert findings[0].filename == str(sub)
    assert findings[0].rule_id == "MATH-04"
    assert findings[0].line == 1


def test_subfile_resolves_cross_file_figure_label(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "\\input{ch1.tex}\n"
        "\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "\\section{First}\n"
        "As seen in Figure~\\ref{fig:myplot}.\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "\\section{Second}\n"
        "\\begin{figure}\n"
        "  \\centering\n"
        "  \\caption{My plot.}\n"
        "  \\label{fig:myplot}\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )

    findings = check(ch2, rule_filter=["FIG-03"])
    assert findings == []


def test_subfile_excludes_root_violations(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass[draft]{report}\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text(
        "\\section{Chapter}\n"
        "Clean prose here.\n",
        encoding="utf-8",
    )

    findings_root = check(root, rule_filter=["WORK-03"])
    assert len(findings_root) == 1
    assert findings_root[0].rule_id == "WORK-03"

    findings_sub = check(sub, rule_filter=["WORK-03"])
    assert findings_sub == []


def test_subfile_magic_comment_root(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    sub = chapters / "intro.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "$\\frac{1}{2}$\n"
        "\\input{chapters/intro.tex}\n",
        encoding="utf-8",
    )
    sub.write_text(
        "% !TeX root = ../main.tex\n"
        "$\\frac{3}{4}$\n",
        encoding="utf-8",
    )

    findings = check(sub)
    assert len(findings) == 1
    assert findings[0].filename == str(sub)
    assert findings[0].rule_id == "MATH-04"
    assert findings[0].line == 2


def test_subfile_explicit_root_cli(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "$\\frac{1}{2}$\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    result = run_cli("check", str(sub), "--root", str(root))
    assert result.returncode == 1
    assert str(sub) in result.stdout
    assert str(root) not in result.stdout


def test_subfile_orphan_fallback(tmp_path: Path) -> None:
    orphan = tmp_path / "orphan.tex"
    orphan.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    findings = check(orphan)
    assert len(findings) == 1
    assert findings[0].filename == str(orphan)
    assert findings[0].rule_id == "MATH-04"


def test_subfile_cli_filtering(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "$\\frac{1}{2}$\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    result = run_cli("check", str(sub))
    assert result.returncode == 1
    assert str(sub) in result.stdout
    assert str(root) not in result.stdout


def test_subfile_deeply_nested_directory(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub_dir = tmp_path / "chapters" / "deep"
    sub_dir.mkdir(parents=True)
    sub = sub_dir / "section.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "\\input{chapters/deep/section.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    findings = check(sub)
    assert len(findings) == 1
    assert findings[0].filename == str(sub)


def test_subfile_suppression_applies_within_file(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    sub = tmp_path / "chapter.tex"
    root.write_text(
        "\\documentclass{report}\n"
        "\\input{chapter.tex}\n",
        encoding="utf-8",
    )
    sub.write_text("$\\frac{3}{4}$ % latex-lint:ignore=MATH-04\n", encoding="utf-8")

    findings = check(sub)
    assert findings == []


def test_bib_file_direct_check_preserves_findings(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        "@article{knuth1984,\n"
        "  author = {Donald E. Knuth},\n"
        "  title = {Literate Programming}\n"
        "}\n",
        encoding="utf-8",
    )

    findings = check(bib, rule_filter=["CITE-08"])
    assert len(findings) >= 1
    assert all(f.filename == str(bib) for f in findings)
