from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_prose_02_metadata() -> None:
    rule = get_rule("PROSE-02")
    assert rule.rule_id == "PROSE-02"
    assert "referent noun" in rule.explanation
    assert "referent noun" in rule.correction
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "heuristic" in rule.limits.lower()


@pytest.mark.parametrize(
    ("text", "expected_col"),
    [
        ("This is an important result.", 1),
        ("These are important results.", 1),
        ("Previous sentence. This shows high accuracy.", 20),
        ("Previous sentence. These show high accuracy.", 20),
        ("Previous sentence. This demonstrates validity.", 20),
        ("Previous sentence. These demonstrate validity.", 20),
        ("Previous sentence. This indicates progress.", 20),
        ("Previous sentence. These indicate progress.", 20),
        ("Previous sentence. This leads to instability.", 20),
        ("Previous sentence. These lead to instability.", 20),
        ("Previous sentence. This means that it works.", 20),
        ("Previous sentence. These mean that it works.", 20),
        ("Previous sentence. This suggests a pattern.", 20),
        ("Previous sentence. These suggest a pattern.", 20),
        ("Previous sentence. This illustrates the idea.", 20),
        ("Previous sentence. These illustrate the idea.", 20),
        ("Previous sentence. This proves the theorem.", 20),
        ("Previous sentence. These prove the theorem.", 20),
        ("Previous sentence. This was observed.", 20),
        ("Previous sentence. These were observed.", 20),
        ("Previous sentence. This has shown success.", 20),
        ("Previous sentence. These have shown success.", 20),
        ("Previous sentence. This will improve.", 20),
        ("Previous sentence. These will improve.", 20),
        ("Previous sentence. This can be seen.", 20),
        ("Previous sentence. These can be seen.", 20),
        ("Previous sentence. This could explain it.", 20),
        ("Previous sentence. These could explain it.", 20),
        ("Previous sentence. This would require time.", 20),
        ("Previous sentence. These would require time.", 20),
        ("Question? This is a finding.", 11),
        ("Important! This shows results.", 12),
        ("Note: This indicates success.", 7),
        ("First part; This proves it.", 13),
        ("(This is a parenthetical finding.)", 2),
    ],
)
def test_prose_02_violations(text: str, expected_col: int, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(text + "\n", encoding="utf-8")
    findings = check(root)
    prose_02 = [f for f in findings if f.rule_id == "PROSE-02"]
    assert len(prose_02) == 1
    finding = prose_02[0]
    assert finding.filename == str(root)
    assert finding.line == 1
    assert finding.column == expected_col
    assert "referent noun" in finding.explanation
    assert "referent noun" in finding.correction


@pytest.mark.parametrize(
    "source",
    [
        "This approach is effective.",
        "This method shows high accuracy.",
        "These results demonstrate validity.",
        "These findings are significant.",
        "This system was evaluated.",
        "These experiments have shown success.",
        "This architecture will improve performance.",
        "This model can be seen in Figure 1.",
        "These techniques could explain the discrepancy.",
        "In this section, we show the results.",
        "We consider this.",
        "% This is a comment.",
        "\\begin{verbatim}This is code\\end{verbatim}",
        "\\verb|This is code|",
        "$This is math$",
        "\\label{sec:this_is_it}",
        "\\cite{this_key}",
    ],
)
def test_prose_02_valid_counterparts(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source + "\n", encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-02"] == []


def test_prose_02_multiline(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "This\nshows high accuracy.\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_02 = [f for f in findings if f.rule_id == "PROSE-02"]
    assert len(prose_02) == 1
    assert (prose_02[0].line, prose_02[0].column) == (1, 1)


def test_prose_02_after_heading(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "\\section{Introduction}\nThis is the beginning.\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    prose_02 = [f for f in findings if f.rule_id == "PROSE-02"]
    assert len(prose_02) == 1
    assert (prose_02[0].line, prose_02[0].column) == (2, 1)


def test_prose_02_same_line_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = "This is acceptable here. % latex-lint:ignore=PROSE-02\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [f for f in findings if f.rule_id == "PROSE-02"] == []
