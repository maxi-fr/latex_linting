from pathlib import Path

import pytest

from latex_linting.cli import main as cli_main
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_cite_07_metadata() -> None:
    rule = get_rule("CITE-07")
    assert rule.rule_id == "CITE-07"
    assert "consecutive" in rule.explanation.lower()
    assert "redundant" in rule.explanation.lower()
    assert rule.enabled_by_default is True
    assert rule.severity == "error"
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "paragraph" in rule.limits.lower()


def test_cite_07_subsequent_sentences_violation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one establishes the foundational architecture~\\cite{smith2020}. "
        "Sentence two details its performance gains~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert len(findings) == 1
    assert findings[0].line == 1
    assert findings[0].column == 56  # The first \cite token
    assert "smith2020" in findings[0].explanation


def test_cite_07_same_sentence_violation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "First part of sentence~\\cite{smith2020}, and second part~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert len(findings) == 1
    assert findings[0].column == 24


def test_cite_07_three_consecutive_violations(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Part one~\\cite{ref1}. Part two~\\cite{ref1}. Part three~\\cite{ref1}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert len(findings) == 2
    assert findings[0].column == 10
    assert findings[1].column == 32


def test_cite_07_multikey_exact_match_violation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "First sentence~\\cite{smith2020, jones2021}. Second sentence~\\cite{jones2021, smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert len(findings) == 1


def test_cite_07_different_citation_commands_same_key(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "According to~\\citet{smith2020}, convergence holds. Later tests confirmed this~\\citep[p.~5]{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert len(findings) == 1


def test_cite_07_intervening_reference_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence 1~\\cite{ref18}. Sentence 2~\\cite{ref19}. Sentence 3~\\cite{ref18}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_intervening_sentence_without_citation_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one establishes the foundational architecture~\\cite{smith2020}. "
        "Sentence two describes the training procedures and numerical setup without citing. "
        "Sentence three evaluates the model performance~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_intervening_reference_same_sentence_passes(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "first_part~\\cite{ref18}, second_part~\\cite{ref19}. Sentence 2~\\cite{ref18}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_multikey_subset_not_flagged(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence 1~\\cite{ref18, ref19}. Sentence 2~\\cite{ref18}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_paragraph_break_resets(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one~\\cite{smith2020}.\n\nSentence two~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_par_command_resets(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one~\\cite{smith2020}.\\par Sentence two~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_heading_resets(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one~\\cite{smith2020}.\n\\section{New Section}\nSentence two~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_item_resets(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{itemize}\n"
        "\\item First item~\\cite{smith2020}.\n"
        "\\item Second item~\\cite{smith2020}.\n"
        "\\end{itemize}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_float_caption_resets(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{figure}\n"
        "\\caption{Diagram of system~\\cite{smith2020}.}\n"
        "\\end{figure}\n"
        "In the main text we discuss the system~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Sentence one~\\cite{smith2020}. % latex-lint: ignore=CITE-07\nSentence two~\\cite{smith2020}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "CITE-07"]
    assert findings == []


def test_cite_07_cli_rule_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["rule", "CITE-07"]) == 0
    captured = capsys.readouterr()
    assert "CITE-07" in captured.out
    assert "redundant" in captured.out.lower()
