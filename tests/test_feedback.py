from pathlib import Path

import pytest

from latex_linting.cli import main
from latex_linting.document import load_document
from latex_linting.feedback import extract_feedback_lines


def test_empty_and_filtered_comments(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "% \n"
        "%%%\n"
        "% latex-lint:ignore=MATH-04\n"
        "% latex-lint:disable=TYPO-01\n"
        "% latex-lint:enable=TYPO-01\n"
        "% cite-checked: author2020=SUPPORTED\n"
        "% citation-checked: author2020=SUPPORTED\n"
        "% cite-checked\n"
        "% citation-checked\n"
        "Some text without feedback.\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == []


def test_inline_comment(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "We introduce the model here. % check this claim\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:2: We introduce the model here. % check this claim",
    ]


def test_inline_comment_filtered_unless_feedback_present(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "$a/b$ % latex-lint:ignore=MATH-04\n"
        "$\\cite{foo}$ % cite-checked: foo=SUPPORTED\n"
        "$c/d$ % latex-lint:ignore=MATH-04 % please review fraction\n"
        "$\\cite{bar}$ % cite-checked: bar=SUPPORTED % double-check year\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:4: $c/d$ % latex-lint:ignore=MATH-04 % please review fraction",
        f"{tex}:5: $\\cite{{bar}}$ % cite-checked: bar=SUPPORTED % double-check year",
    ]


def test_section_start_comment_with_and_without_label(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "\\section{Introduction}\n"
        "\\label{sec:intro}\n"
        "% Rewrite motivation in this section.\n"
        "First sentence of the introduction.\n"
        "\n"
        "\\subsection{Background}\n"
        "% Add prior work here.\n"
        "Background details.\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:2: \\section{{Introduction}}",
        f"{tex}:4: % Rewrite motivation in this section.",
        f"{tex}:7: \\subsection{{Background}}",
        f"{tex}:8: % Add prior work here.",
    ]


def test_post_paragraph_comment(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "\\section{Results}\n"
        "The model achieves 95 percent accuracy.\n"
        "This outperforms previous benchmarks.\n"
        "% Explain error bars.\n"
        "\n"
        "Another paragraph begins here.\n"
        "It has two sentences.\n"
        "\n"
        "% Check statistical significance.\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:3: The model achieves 95 percent accuracy.",
        f"{tex}:4: This outperforms previous benchmarks.",
        f"{tex}:5: % Explain error bars.",
        f"{tex}:7: Another paragraph begins here.",
        f"{tex}:8: It has two sentences.",
        f"{tex}:10: % Check statistical significance.",
    ]


def test_multi_line_comment_grouping(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "\\section{Discussion}\n"
        "% Point 1 to expand.\n"
        "% Point 2 to expand.\n"
        "Discussion text.\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:2: \\section{{Discussion}}",
        f"{tex}:3: % Point 1 to expand.",
        f"{tex}:4: % Point 2 to expand.",
    ]


def test_comment_before_section_belongs_to_preceding_block(tmp_path: Path) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "Final paragraph of chapter.\n"
        "% Clarify conclusion.\n"
        "\\section{Next Chapter}\n"
        "Opening text.\n",
        encoding="utf-8",
    )
    doc = load_document(tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{tex}:2: Final paragraph of chapter.",
        f"{tex}:3: % Clarify conclusion.",
    ]


def test_document_with_included_files(tmp_path: Path) -> None:
    main_tex = tmp_path / "main.tex"
    ch1_tex = tmp_path / "ch1.tex"
    ch2_tex = tmp_path / "ch2.tex"

    main_tex.write_text(
        "\\documentclass{report}\n"
        "\\input{ch1.tex}\n"
        "\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1_tex.write_text(
        "\\chapter{One}\n"
        "% Check chapter 1 overview.\n"
        "Chapter 1 content.\n",
        encoding="utf-8",
    )
    ch2_tex.write_text(
        "\\chapter{Two}\n"
        "Sentence in ch2. % inline note in ch2\n",
        encoding="utf-8",
    )
    doc = load_document(main_tex)
    lines = extract_feedback_lines(doc)
    assert lines == [
        f"{ch1_tex}:1: \\chapter{{One}}",
        f"{ch1_tex}:2: % Check chapter 1 overview.",
        f"{ch2_tex}:2: Sentence in ch2. % inline note in ch2",
    ]


def test_cli_feedback_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tex = tmp_path / "doc.tex"
    tex.write_text(
        "\\documentclass{report}\n"
        "\\section{Method}\n"
        "% Clarify methodology.\n",
        encoding="utf-8",
    )
    exit_code = main(["feedback", str(tex)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == f"{tex}:2: \\section{{Method}}\n{tex}:3: % Clarify methodology.\n"
    assert captured.err == ""


def test_cli_feedback_missing_file(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["feedback", "nonexistent.tex"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "nonexistent.tex" in captured.err
