from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_01_metadata() -> None:
    rule = get_rule("TYPO-01")
    assert rule.rule_id == "TYPO-01"
    assert "nonbreaking" in rule.explanation.lower()
    assert "~" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "optional" in rule.limits.lower()


def test_valid_reference_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("As shown in Figure~\\ref{fig:arch}, the system operates.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_citation_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("According to Smith~\\cite{smith2020}, this holds.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_citation_commands_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "Work by Smith~\\citep{smith2020} and Jones~\\citet{jones2021} proves this.\n"
        "Recent advances~\\autocite{doe2022} and others~\\parencite{lee2023} agree.\n"
        "As discussed in~\\textcite{brown2024}, the bounds hold.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_reference_commands_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "See Equation~\\eqref{eq:1} and Section~\\autoref{sec:intro}.\n"
        "Compare Section~\\cref{sec:methods} and Figure~\\Cref{fig:arch}.\n"
        "Refer to page~\\pageref{sec:intro} for details.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_invalid_reference_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("As shown in Figure \\ref{fig:arch}, the system operates.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-01"
    assert findings[0].line == 1
    assert findings[0].column == 20
    assert "\\ref{fig:arch}" in findings[0].excerpt


def test_invalid_citation_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("According to Smith \\cite{smith2020}, this holds.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-01"
    assert findings[0].line == 1
    assert findings[0].column == 20


def test_invalid_reference_line_break_without_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("As shown in Figure\n\\ref{fig:arch}, the system operates.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 1
    assert findings[0].rule_id == "TYPO-01"
    assert findings[0].line == 2
    assert findings[0].column == 1


def test_valid_reference_line_break_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("As shown in Figure~\n\\ref{fig:arch}, the system operates.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_command_at_sentence_start(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\ref{sec:intro} presents the core contributions.\n"
        "Previous sentence ended here. \\ref{fig:arch} shows the diagram.\n"
        "Another result was found! \\cite{smith2020} confirmed it.\n"
        "Can we do this? \\citet{jones2021} argued yes.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_command_at_sentence_start_across_line_break(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "The previous sentence ended here.\n\\ref{fig:arch} shows the architecture.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_command_after_blank_line(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "First paragraph.\n\n\\ref{fig:arch} begins the second paragraph.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_valid_command_at_parenthesis_or_bracket(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "The diagram (\\ref{fig:arch}) illustrates the pipeline.\n"
        "Prior work [\\cite{smith2020}] is relevant.\n"
        "Grouped {\\ref{fig:arch}} passes.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_citation_optional_argument_handling(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "Valid citation~\\cite[p.~5]{smith2020}.\n"
        "Invalid citation \\cite[p.~5]{smith2020}.\n"
        "Valid natbib~\\citep[see][p.~10]{jones2021}.\n"
        "Invalid natbib \\citep[see][p.~10]{jones2021}.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 2
    assert findings[0].line == 2
    assert findings[1].line == 4


def test_reference_inside_optional_argument(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\begin{itemize}\n"
        "\\item[\\ref{step1}] First item.\n"
        "\\item[Step \\ref{step2}] Second item.\n"
        "\\item[Step~\\ref{step3}] Third item.\n"
        "\\end{itemize}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 1
    assert findings[0].line == 3


def test_abbreviation_period_does_not_mask_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "As noted by Smith et al. \\cite{smith2020}, this holds.\nFor example, e.g. \\ref{fig:1} demonstrates this.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 2


def test_comments_and_literals_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "% Figure \\ref{fig:arch}\n"
        "\\begin{verbatim}\n"
        "Figure \\ref{fig:arch}\n"
        "Smith \\cite{smith2020}\n"
        "\\end{verbatim}\n"
        "Figure~% a comment\n"
        "\\ref{fig:arch} is shown.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_math_mode_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("$x = \\ref{eq:1} + \\eqref{eq:2}$\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_same_line_ignore_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("Figure \\ref{fig:arch} % latex-lint:ignore=TYPO-01\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=TYPO-01\nFigure \\ref{fig:1}\n% latex-lint:enable=TYPO-01\nFigure \\ref{fig:2}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-01"]
    assert len(findings) == 1
    assert findings[0].line == 4
