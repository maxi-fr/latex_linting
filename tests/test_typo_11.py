from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_valid_chronological_equation_reference(tmp_path: Path) -> None:
    """Accept equation reference appearing after equation definition."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n"
        "\\label{eq:first}\n"
        "  a = b \\,.\n"
        "\\end{equation}\n"
        "As established in~\\eqref{eq:first}, the model holds.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert findings == []


def test_valid_cross_file_chronological_reference(tmp_path: Path) -> None:
    """Accept equation reference in later included file after definition in earlier file."""
    root = tmp_path / "thesis.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"
    root.write_text(
        "\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "\\begin{equation}\n\\label{eq:ch1_eq}\n  x = y \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "Recalling~\\eqref{eq:ch1_eq}, we proceed.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert findings == []


def test_invalid_forward_equation_reference(tmp_path: Path) -> None:
    """Flag equation reference appearing before its definition in same file."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As will be shown in~\\eqref{eq:later}, the model holds.\n"
        "\\begin{equation}\n"
        "\\label{eq:later}\n"
        "  a = b \\,.\n"
        "\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-11"
    assert findings[0].line == 1
    assert "\\eqref{eq:later}" in findings[0].excerpt


def test_invalid_forward_reference_via_ref(tmp_path: Path) -> None:
    """Flag forward reference to equation even when using ref instead of eqref."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Equation~\\ref{eq:future}.\n\\begin{equation}\n\\label{eq:future}\n  a = b \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-11"


def test_invalid_cross_file_forward_reference(tmp_path: Path) -> None:
    """Flag equation reference in earlier included file before definition in later file."""
    root = tmp_path / "thesis.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"
    root.write_text(
        "\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "We preview~\\eqref{eq:ch2_eq} here.\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "\\begin{equation}\n\\label{eq:ch2_eq}\n  x = y \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-11"
    assert "ch1.tex" in findings[0].filename


def test_multiple_forward_references_flagged(tmp_path: Path) -> None:
    """Flag all forward occurrences before the equation is introduced."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "First preview in~\\eqref{eq:future}.\n"
        "Second preview in~\\eqref{eq:future}.\n"
        "\\begin{equation}\n"
        "\\label{eq:future}\n"
        "  a = b \\,.\n"
        "\\end{equation}\n"
        "Post-definition reference in~\\eqref{eq:future}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert len(findings) == 2
    assert [f.line for f in findings] == [1, 2]


def test_non_equation_references_ignored(tmp_path: Path) -> None:
    """Ignore non-equation references even if text precedes float definition."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As shown in Table~\\ref{tab:preview}, the values vary.\n"
        "\\begin{table}\n"
        "  \\caption{Preview table.}\n"
        "  \\label{tab:preview}\n"
        "  \\begin{tabular}{ll}\n"
        "    1 & 2 \\\\\n"
        "  \\end{tabular}\n"
        "\\end{table}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert findings == []


def test_undefined_equation_not_flagged_as_forward(tmp_path: Path) -> None:
    """Do not flag undefined equation label as forward reference."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Reference to undefined equation~\\eqref{eq:nonexistent}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Respect line-level suppression directive."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Preview in~\\eqref{eq:later}. % latex-lint:ignore=TYPO-11\n"
        "\\begin{equation}\n"
        "\\label{eq:later}\n"
        "  a = b \\,.\n"
        "\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-11"]
    assert findings == []


def test_metadata_and_catalogue() -> None:
    """Verify TYPO-11 metadata registration and rule retrieval."""
    rule = get_rule("TYPO-11")
    assert rule.rule_id == "TYPO-11"
    assert rule.explanation
    assert rule.correction
    assert rule.limits
