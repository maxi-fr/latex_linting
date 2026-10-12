import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.source import Finding, Source

_CHKTEX_FIELD_COUNT = 5
_LACHECK_RE = re.compile(r'^(?:"([^"]+)"|([^\s,:]+)),\s*line\s*(\d+):\s*(.*)$')
_LACHECK_AT_RE = re.compile(r'at\s+"([^"]+)"')


def _build_sources_map(document: "Document", base_dir: Path) -> dict[Path, Source]:
    mapping: dict[Path, Source] = {}
    for source in document.sources:
        p = Path(source.filename)
        resolved = p.resolve() if p.is_absolute() else (base_dir / p).resolve()
        mapping[resolved] = source
    return mapping


def run_chktex(document: "Document") -> list[Finding]:
    """Execute ChkTeX on the root LaTeX document and return parsed findings."""
    chktex_bin = shutil.which("chktex")
    if chktex_bin is None:
        sys.stderr.write("latex-lint: warning: 'chktex' executable not found on PATH, skipping ChkTeX\n")
        return []

    root_path = Path(document.root_node.source.filename)
    base_dir = root_path.parent.resolve()
    target_name = root_path.name
    sources_map = _build_sources_map(document, base_dir)

    cmd = [chktex_bin, "-q", "-I1", "-f%f|%l|%c|%n|%m\n", target_name]
    proc = subprocess.run(  # noqa: S603 -- invoke system chktex with validated arguments
        cmd,
        cwd=base_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    findings: list[Finding] = []
    for line in proc.stdout.splitlines():
        parts = line.split("|", 4)
        if len(parts) != _CHKTEX_FIELD_COUNT:
            continue
        raw_file, raw_line, raw_col, raw_num, raw_msg = parts
        file_str = raw_file.strip()
        num_str = raw_num.strip()
        msg = raw_msg.strip()
        rule_id = f"CHKTEX-{num_str}"

        try:
            line_num = int(raw_line.strip())
            col_num = int(raw_col.strip())
        except ValueError:
            continue

        resolved = (base_dir / file_str).resolve()
        source = sources_map.get(resolved)
        correction = f"Resolve ChkTeX warning {rule_id}: {msg}"
        if source is not None:
            total_lines = source.line_number(len(source.text))
            line_num = max(1, min(line_num, total_lines))
            line_start = source.offset_of(line_num, 1)
            line_end = source.text.find("\n", line_start)
            line_text = source.text[line_start : line_end if line_end != -1 else len(source.text)].rstrip("\r")
            col_num = max(1, min(col_num, max(1, len(line_text))))
            offset = source.offset_of(line_num, col_num)
            findings.append(source.finding(offset, rule_id, msg, correction))
        else:
            findings.append(Finding(rule_id, file_str, line_num, col_num, "", msg, correction))

    return findings


def run_lacheck(document: "Document") -> list[Finding]:
    """Execute LaCheck on the root LaTeX document and return parsed findings."""
    lacheck_bin = shutil.which("lacheck")
    if lacheck_bin is None:
        sys.stderr.write("latex-lint: warning: 'lacheck' executable not found on PATH, skipping LaCheck\n")
        return []

    root_path = Path(document.root_node.source.filename)
    base_dir = root_path.parent.resolve()
    target_name = root_path.name
    sources_map = _build_sources_map(document, base_dir)

    cmd = [lacheck_bin, target_name]
    proc = subprocess.run(  # noqa: S603 -- invoke system lacheck with validated arguments
        cmd,
        cwd=base_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    findings: list[Finding] = []
    for line in proc.stdout.splitlines():
        match = _LACHECK_RE.match(line)
        if match is None:
            continue
        raw_file = match.group(1) or match.group(2)
        file_str = raw_file.strip()
        try:
            line_num = int(match.group(3))
        except ValueError:
            continue
        msg = match.group(4).strip()
        rule_id = "LACHECK"
        correction = f"Resolve LaCheck warning: {msg}"

        resolved = (base_dir / file_str).resolve()
        source = sources_map.get(resolved)
        if source is not None:
            total_lines = source.line_number(len(source.text))
            line_num = max(1, min(line_num, total_lines))
            line_start = source.offset_of(line_num, 1)
            line_end = source.text.find("\n", line_start)
            line_text = source.text[line_start : line_end if line_end != -1 else len(source.text)].rstrip("\r")

            at_match = _LACHECK_AT_RE.search(msg)
            col_num = 1
            if at_match is not None:
                pattern = at_match.group(1)
                pat_pos = line_text.find(pattern)
                if pat_pos != -1:
                    col_num = pat_pos + 1

            col_num = max(1, min(col_num, max(1, len(line_text))))
            offset = source.offset_of(line_num, col_num)
            findings.append(source.finding(offset, rule_id, msg, correction))
        else:
            findings.append(Finding(rule_id, file_str, line_num, 1, "", msg, correction))

    return findings
