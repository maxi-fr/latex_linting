import shutil
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from latex_linting.compiler import compile_document


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    executable = shutil.which("latex-lint")
    assert executable is not None, "uv must install the latex-lint console command"
    return subprocess.run([executable, *arguments], capture_output=True, text=True, check=False)  # noqa: S603 -- invoke the installed command with test arguments


def test_compile_basic_article(tmp_path: Path) -> None:
    tex_file = tmp_path / "main.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Hello world!
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file))
    assert result.returncode == 0
    out_pdf = tmp_path / "out" / "main.pdf"
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0


def test_compile_subfolder_base_directory(tmp_path: Path) -> None:
    sub = tmp_path / "thesis"
    sub.mkdir()
    tex_file = sub / "thesis.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Chapter 1
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file))
    assert result.returncode == 0
    out_pdf = sub / "out" / "thesis.pdf"
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0


def test_compile_custom_output_dir(tmp_path: Path) -> None:
    tex_file = tmp_path / "main.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
Custom output dir test.
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file), "-o", "build_dir")
    assert result.returncode == 0
    out_pdf = tmp_path / "build_dir" / "main.pdf"
    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0


def test_compile_with_biblatex_and_biber(tmp_path: Path) -> None:
    sub = tmp_path / "paper"
    sub.mkdir()
    tex_file = sub / "paper.tex"
    bib_file = sub / "refs.bib"
    bib_file.write_text(
        r"""@article{knuth1984,
  author = {Donald E. Knuth},
  title = {Literate Programming},
  journal = {The Computer Journal},
  year = {1984},
  volume = {27},
  number = {2},
  pages = {97--111}
}
""",
        encoding="utf-8",
    )
    tex_file.write_text(
        r"""\documentclass{article}
\usepackage{biblatex}
\addbibresource{refs.bib}
\begin{document}
According to Knuth~\cite{knuth1984}.
\printbibliography
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file))
    assert result.returncode == 0
    out_dir = sub / "out"
    assert (out_dir / "paper.pdf").exists()
    assert (out_dir / "paper.bcf").exists()
    assert (out_dir / "paper.bbl").exists()


def test_compile_without_bcf_warns_and_succeeds(tmp_path: Path) -> None:
    tex_file = tmp_path / "nobib.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
No bib here.
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file))
    assert result.returncode == 0
    assert "no .bcf file found" in result.stderr
    assert (tmp_path / "out" / "nobib.pdf").exists()


def test_compile_syntax_error_fails(tmp_path: Path) -> None:
    tex_file = tmp_path / "broken.tex"
    tex_file.write_text(
        r"""\documentclass{article}
\begin{document}
\undefinedcommandthatcancauseerror
\end{document}
""",
        encoding="utf-8",
    )
    result = run_cli("compile", str(tex_file))
    assert result.returncode != 0
    assert not (tmp_path / "out" / "broken.pdf").exists()


def test_compile_missing_root_file(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.tex"
    result = run_cli("compile", str(missing))
    assert result.returncode == 2
    assert "does not exist" in result.stderr


def test_compile_missing_pdflatex(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tex_file = tmp_path / "main.tex"
    tex_file.write_text(r"\documentclass{article}\begin{document}X\end{document}", encoding="utf-8")
    with patch("shutil.which", return_value=None):
        code = compile_document(tex_file)
    assert code == 2
    captured = capsys.readouterr()
    assert "'pdflatex' executable not found" in captured.err


def test_compile_help() -> None:
    main_help = run_cli("--help")
    assert main_help.returncode == 0
    assert "compile" in main_help.stdout
    assert "<root>" in main_help.stdout

    cmd_help = run_cli("compile", "--help")
    assert cmd_help.returncode == 0
    assert "root" in cmd_help.stdout
    assert "--output-dir" in cmd_help.stdout
