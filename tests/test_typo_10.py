from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_valid_figure_reference(tmp_path: Path) -> None:
    """Accept reference preceded by Figure and non-breaking space."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Figure~\\ref{fig:arch} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_abbreviated_figure_reference(tmp_path: Path) -> None:
    """Accept reference preceded by Fig."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Fig.~\\ref{fig:arch} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_german_figure_reference(tmp_path: Path) -> None:
    """Accept German category nouns Abbildung and Abb."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Wie in Abbildung~\\ref{fig:arch} und Abb.~\\ref{fig:model} dargestellt.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_table_reference(tmp_path: Path) -> None:
    """Accept reference preceded by Table or Tabelle."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Table~\\ref{tab:results} and Tabelle~\\ref{tab:metrics}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_section_and_chapter_reference(tmp_path: Path) -> None:
    """Accept references preceded by Section, Chapter, and German counterparts."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "In Section~\\ref{sec:methods} and Chapter~\\ref{cha:intro} as well as Kapitel~\\ref{ch:review}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_pageref(tmp_path: Path) -> None:
    """Accept pageref preceded by page, Seite, or p."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See on page~\\pageref{fig:arch} and auf Seite~\\pageref{sec:methods}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_coordinated_figures(tmp_path: Path) -> None:
    """Accept coordinated figure references sharing preceding plural noun."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Figures~\\ref{fig:a} and~\\ref{fig:b} or Figures~\\ref{fig:a}--\\ref{fig:b}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_coordinated_series(tmp_path: Path) -> None:
    """Accept comma-separated coordinated series with final conjunction."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Figures~\\ref{fig:a}, \\ref{fig:b}, and~\\ref{fig:c}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_parenthetical_reference(tmp_path: Path) -> None:
    """Accept category noun inside opening parenthesis."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The architecture is complex (Figure~\\ref{fig:arch}).\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_valid_generic_prefix(tmp_path: Path) -> None:
    """Accept any recognized category noun when label has no standard prefix."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "According to Theorem~\\ref{thm_main} and Definition~\\ref{def_first}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_exempt_commands(tmp_path: Path) -> None:
    """Exempt autoref, eqref, and equation labels from requiring category noun."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As seen in \\autoref{fig:arch} and in~\\eqref{eq:energy} or \\ref{eq:energy}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_invalid_bare_reference(tmp_path: Path) -> None:
    """Flag reference preceded by preposition or non-category word."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As seen in~\\ref{fig:arch}, the network converges.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-10"
    assert findings[0].line == 1
    assert "\\ref{fig:arch}" in findings[0].excerpt


def test_invalid_sentence_start_reference(tmp_path: Path) -> None:
    """Flag bare reference at beginning of sentence."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\ref{sec:methods} outlines the primary design.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-10"


def test_invalid_mismatched_category(tmp_path: Path) -> None:
    """Flag category noun that contradicts the referenced prefix."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Table~\\ref{fig:arch} for results.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-10"


def test_invalid_pageref(tmp_path: Path) -> None:
    """Flag pageref not preceded by page-related noun."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See on \\pageref{sec:methods} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-10"


def test_invalid_broken_coordination(tmp_path: Path) -> None:
    """Flag coordinated reference when initial reference lacked category noun."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See \\ref{fig:a} and~\\ref{fig:b}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert len(findings) == 2


def test_same_line_suppression(tmp_path: Path) -> None:
    """Respect line-level suppression directive."""
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See \\ref{fig:arch}. % latex-lint:ignore=TYPO-10\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "TYPO-10"]
    assert findings == []


def test_metadata_and_catalogue() -> None:
    """Verify TYPO-10 metadata registration and rule retrieval."""
    rule = get_rule("TYPO-10")
    assert rule.rule_id == "TYPO-10"
    assert rule.explanation
    assert rule.correction
    assert rule.limits
