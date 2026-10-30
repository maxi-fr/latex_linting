import contextlib
import shutil
import subprocess
import sys
from pathlib import Path

RERUN_PATTERNS = (
    "LaTeX Warning: Label(s) may have changed. Rerun to get cross-references right.",
    "LaTeX Warning: There were undefined references.",
    "Rerun to get outlines right",
)


def _run_biber(
    out_path: Path,
    doc_stem: str,
    base_dir: Path,
    *,
    verbose: bool,
) -> int:
    """Run biber on the generated .bcf control file if present."""
    bcf_path = out_path / f"{doc_stem}.bcf"
    if not bcf_path.exists():
        sys.stderr.write(f"latex-lint: warning: no .bcf file found at '{bcf_path}', skipping biber\n")
        return 0

    biber_bin = shutil.which("biber")
    if biber_bin is None:
        sys.stderr.write("latex-lint: warning: 'biber' executable not found on PATH, skipping biber\n")
        return 0

    biber_cmd = [
        biber_bin,
        f"--input-directory={out_path}",
        f"--output-directory={out_path}",
        doc_stem,
    ]
    biber_proc = subprocess.run(  # noqa: S603 -- invoke system biber with validated arguments
        biber_cmd,
        cwd=base_dir,
        capture_output=not verbose,
        text=True,
        check=False,
    )
    if biber_proc.returncode != 0:
        sys.stderr.write(f"latex-lint: warning: biber exited with code {biber_proc.returncode}\n")
        if not verbose:
            if biber_proc.stdout:
                sys.stderr.write(biber_proc.stdout)
            if biber_proc.stderr:
                sys.stderr.write(biber_proc.stderr)
    return biber_proc.returncode


def _log_contains(log_path: Path, pattern: str) -> bool:
    """Check if the log file contains the given substring."""
    if not log_path.exists():
        return False
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    else:
        return pattern in content


def _needs_rerun(log_path: Path) -> bool:
    """Check if LaTeX logged warnings requesting another compilation pass."""
    if not log_path.exists():
        return False
    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    else:
        return any(pattern in content for pattern in RERUN_PATTERNS)


def _resolve_out_path(
    base_dir: Path,
    out_dir: str | Path | None,
    *,
    force: bool = False,
) -> Path:
    """Resolve, clean if forced, and create output directories."""
    if out_dir is not None:
        out_p = Path(out_dir)
        out_path = out_p.resolve() if out_p.is_absolute() else (base_dir / out_p).resolve()
    else:
        out_path = (base_dir / "out").resolve()

    if force and out_path.exists():
        for item in out_path.iterdir():
            if item.is_file():
                item.unlink(missing_ok=True)
            elif item.is_dir():
                shutil.rmtree(item, ignore_errors=True)

    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "figures").mkdir(parents=True, exist_ok=True)
    return out_path


def _run_pdflatex(
    pdflatex_bin: str,
    root_path: Path,
    out_path: Path,
    base_dir: Path,
    *,
    verbose: bool,
) -> int:
    """Run a single pass of pdflatex."""
    cmd = [
        pdflatex_bin,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-synctex=1",
        "-recorder",
        "-shell-escape",
        f"-output-directory={out_path}",
        str(root_path.resolve()),
    ]
    proc = subprocess.run(  # noqa: S603 -- invoke system pdflatex with validated arguments
        cmd,
        cwd=base_dir,
        capture_output=not verbose,
        text=True,
        check=False,
    )
    if proc.returncode != 0 and not verbose:
        if proc.stdout:
            sys.stderr.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
    return proc.returncode


def _run_full_recipe(
    pdflatex_bin: str,
    root_path: Path,
    out_path: Path,
    base_dir: Path,
    *,
    verbose: bool,
) -> int:
    """Run the complete unconditional multi-pass recipe from scratch."""
    _run_biber(out_path, root_path.stem, base_dir, verbose=verbose)
    res = _run_pdflatex(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)
    if res != 0:
        return res
    return _run_pdflatex(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)


def _run_followup_passes(
    pdflatex_bin: str,
    root_path: Path,
    out_path: Path,
    base_dir: Path,
    *,
    verbose: bool,
) -> int:
    """Conditionally run Biber and subsequent pdflatex passes when needed."""
    doc_stem = root_path.stem
    log_path = out_path / f"{doc_stem}.log"
    bcf_path = out_path / f"{doc_stem}.bcf"
    bbl_path = out_path / f"{doc_stem}.bbl"

    if not bcf_path.exists():
        _run_biber(out_path, doc_stem, base_dir, verbose=verbose)
    elif not bbl_path.exists() or _log_contains(log_path, "Please (re)run Biber on the file"):
        _run_biber(out_path, doc_stem, base_dir, verbose=verbose)
        res = _run_pdflatex(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)
        if res != 0:
            return res

    if _needs_rerun(log_path):
        return _run_pdflatex(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)

    return 0


def _cleanup_stray_artifacts(base_dir: Path, out_path: Path) -> None:
    """Ensure stray root artifacts like pdfa.xmpi are moved into out_path."""
    stray_xmpi = base_dir / "pdfa.xmpi"
    if stray_xmpi.exists():
        out_xmpi = out_path / "pdfa.xmpi"
        if not out_xmpi.exists():
            with contextlib.suppress(OSError):
                shutil.move(str(stray_xmpi), str(out_xmpi))
        else:
            stray_xmpi.unlink(missing_ok=True)


def compile_document(
    root: str | Path,
    out_dir: str | Path | None = None,
    *,
    verbose: bool = False,
    force: bool = False,
) -> int:
    """Compile a LaTeX document using dynamic smart rerun or full force mode."""
    root_path = Path(root)
    if not root_path.exists() or not root_path.is_file():
        sys.stderr.write(f"latex-lint: root document '{root}' does not exist\n")
        return 2

    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin is None:
        sys.stderr.write("latex-lint: 'pdflatex' executable not found on PATH\n")
        return 2

    base_dir = root_path.parent.resolve()
    out_path = _resolve_out_path(base_dir, out_dir, force=force)

    try:
        res = _run_pdflatex(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)
        if res != 0:
            return res

        if force:
            return _run_full_recipe(pdflatex_bin, root_path, out_path, base_dir, verbose=verbose)

        return _run_followup_passes(
            pdflatex_bin,
            root_path,
            out_path,
            base_dir,
            verbose=verbose,
        )
    finally:
        _cleanup_stray_artifacts(base_dir, out_path)
