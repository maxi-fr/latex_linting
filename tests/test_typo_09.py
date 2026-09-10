from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_figure_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n  \\caption{Architecture diagram}\n  \\label{fig:arch}\n\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_valid_figure_star_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure*}\n  \\caption{Wide diagram}\n  \\label{fig:wide}\n\\end{figure*}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_figure_label_nonstandard(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n  \\caption{Diagram}\n  \\label{my_arch}\n\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"
    assert findings[0].line == 3
    assert findings[0].column == 3
    assert "\\label{my_arch}" in findings[0].excerpt


def test_invalid_figure_label_wrong_prefix(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n  \\caption{Diagram}\n  \\label{tab:diagram}\n\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


def test_valid_table_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n  \\caption{Results table}\n  \\label{tab:results}\n\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_table_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{table}\n  \\caption{Results table}\n  \\label{results}\n\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


def test_valid_equation_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:einstein}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_equation_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{formula1}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"
    assert findings[0].line == 3


def test_valid_chapter_label_ch(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\chapter{Introduction}\n\\label{ch:intro}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_valid_chapter_label_cha(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\chapter{Introduction}\n\\label{cha:intro}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_chapter_label_sec(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\chapter{Introduction}\n\\label{sec:intro}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


def test_invalid_chapter_label_bare(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\chapter{Introduction}\n\\label{intro}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


@pytest.mark.parametrize("heading", ["section", "subsection", "subsubsection"])
def test_valid_section_labels(tmp_path: Path, heading: str) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        f"\\{heading}{{Methods}}\n\\label{{sec:methods}}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_section_label_ch(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\section{Methods}\n\\label{ch:methods}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


def test_valid_unknown_context_standard_prefixes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Some text.\n\\label{app:appendix_a}\n\\label{lst:python_code}\n\\label{listing:rust_code}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invalid_unknown_context_prefix(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Some text.\n\\label{custom_prefix}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-09"


def test_comment_and_verbatim_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% \\label{bad_in_comment}\n\\begin{verbatim}\n\\label{bad_in_verbatim}\n\\end{verbatim}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n  \\caption{Diagram}\n  \\label{bad_figure} % latex-lint:ignore=TYPO-09\n\\end{figure}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=TYPO-09\n"
        "\\begin{figure}\n"
        "  \\caption{Diagram}\n"
        "  \\label{bad_figure}\n"
        "\\end{figure}\n"
        "% latex-lint:enable=TYPO-09\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-09"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n  \\caption{Diagram}\n  \\label{bad_figure}\n\\end{figure}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["TYPO-09"])
    assert not any(f.rule_id == "TYPO-09" for f in findings)
