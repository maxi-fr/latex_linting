import shutil
import subprocess
import sys
from pathlib import Path


def _run_biber(
    out_path: Path,
    doc_stem: str,
    base_dir: Path,
    *,
    capture_output: bool,
) -> None:
    """Run biber on the generated .bcf control file if present."""
    bcf_path = out_path / f"{doc_stem}.bcf"
    if not bcf_path.exists():
        sys.stderr.write(f"latex-lint: warning: no .bcf file found at '{bcf_path}', skipping biber\n")
        return

    biber_bin = shutil.which("biber")
    if biber_bin is None:
        sys.stderr.write("latex-lint: warning: 'biber' executable not found on PATH, skipping biber\n")
        return

    biber_cmd = [
        biber_bin,
        f"--input-directory={out_path}",
        f"--output-directory={out_path}",
        doc_stem,
    ]
    biber_proc = subprocess.run(  # noqa: S603 -- invoke system biber with validated arguments
        biber_cmd,
        cwd=base_dir,
        capture_output=capture_output,
        text=True,
        check=False,
    )
    if biber_proc.returncode != 0:
        sys.stderr.write(f"latex-lint: warning: biber exited with code {biber_proc.returncode}\n")


def compile_document(
    root: str | Path,
    out_dir: str | Path | None = None,
    *,
    capture_output: bool = False,
) -> int:
    """Compile a LaTeX document using the recipe: pdflatex, biber, pdflatex, pdflatex."""
    root_path = Path(root)
    if not root_path.exists() or not root_path.is_file():
        sys.stderr.write(f"latex-lint: root document '{root}' does not exist\n")
        return 2

    base_dir = root_path.parent.resolve()
    tex_filename = root_path.name
    doc_stem = root_path.stem

    if out_dir is not None:
        out_p = Path(out_dir)
        out_path = out_p.resolve() if out_p.is_absolute() else (base_dir / out_p).resolve()
    else:
        out_path = (base_dir / "out").resolve()

    out_path.mkdir(parents=True, exist_ok=True)

    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin is None:
        sys.stderr.write("latex-lint: 'pdflatex' executable not found on PATH\n")
        return 2

    def run_pdflatex() -> int:
        cmd = [
            pdflatex_bin,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={out_path}",
            tex_filename,
        ]
        proc = subprocess.run(  # noqa: S603 -- invoke system pdflatex with validated arguments
            cmd,
            cwd=base_dir,
            capture_output=capture_output,
            text=True,
            check=False,
        )
        return proc.returncode

    res = run_pdflatex()
    if res != 0:
        return res

    _run_biber(out_path, doc_stem, base_dir, capture_output=capture_output)

    res = run_pdflatex()
    if res != 0:
        return res

    return run_pdflatex()
