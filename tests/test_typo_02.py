from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_02_metadata() -> None:
    rule = get_rule("TYPO-02")
    assert rule.rule_id == "TYPO-02"
    assert "nonbreaking" in rule.explanation.lower()
    assert "~" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "figure" in rule.limits.lower()


def test_valid_fixed_expressions_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "As seen in Figure~1, Table~2, Section~3, and Chapter~4.\n"
        "Also Fig.~1, Tab.~2, Sec.~3, Ch.~4, and Eq.~5.\n"
        "Subsections Section~1.2 and Figure~4.2 are valid.\n"
        "Plural forms Figures~1 and Tables~2 are valid.\n"
        "Page references Page~5 and p.~10 are valid.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_invalid_fixed_expressions_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "As seen in Figure 1 and Table 2.\n"
        "In Section 3 and Chapter 4.\n"
        "Also Fig. 1, Tab. 2, Sec. 3, and Ch. 4.\n"
        "See Equation 5, Eq. 6, Page 7, and p. 8.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 12
    assert findings[0].line == 1
    assert "\n" not in findings[0].excerpt


def test_invalid_fixed_expression_line_break(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("As shown in Figure\n1, the system works.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 1
    assert findings[0].line == 1


def test_valid_titles_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "Dr.~Müller and Prof.~Smith gave the lecture.\nMr.~Jones, Ms.~Davis, and Mrs.~White attended.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_invalid_titles_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "Dr. Müller and Prof. Smith gave the lecture.\nMr. Jones, Ms. Davis, and Mrs. White attended.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 5


def test_valid_times_with_tilde(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "The meeting is at 3~p.m. or 10~a.m.\nIn German, it starts at 3~Uhr.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_invalid_times_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "The meeting is at 3 p.m. or 10 a.m.\nIn German, it starts at 3 Uhr.\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 3


def test_valid_number_unit_in_text(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "The distance is 10~m or 5~kg or 20~s.\n"
        "Using thin space: 10\\,m, 5\\,kg, 100\\,V, 50\\,Hz.\n"
        "Using siunitx: \\SI{10}{m} or \\qty{5}{kg}.\n"
        "Regular non-units: 10 apples, 5 dogs, in 2020 he left.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_invalid_number_unit_in_text_regular_space(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "The distance is 10 m and the mass is 5 kg.\n"
        "The duration was 20 s at 100 V and 50 Hz.\n"
        "The track is 3.5 km long with 5 dB attenuation.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 7


def test_math_mode_not_flagged_by_typo_02(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("In equation $10 m$ or $5 kg$, math mode applies.\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_syntax_command_arguments_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\label{fig:1}\n\\label{tab:1}\n\\label{sec:1}\n\\ref{fig:1}\n\\cite{paper1}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_comments_and_literal_blocks_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% Figure 1 is commented\n\\begin{verbatim}\nFigure 1\n10 m\nDr. Müller\n\\end{verbatim}\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_same_line_ignore_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text("See Figure 1 % latex-lint:ignore=TYPO-02\n", encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "% latex-lint:disable=TYPO-02\nFigure 1\n% latex-lint:enable=TYPO-02\nFigure 2\n"
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-02"]
    assert len(findings) == 1
    assert findings[0].line == 4
