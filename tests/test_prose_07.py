from pathlib import Path

from latex_linting.main import check


def test_valid_equation_without_colon(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The energy relation is\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_valid_bracket_math_without_colon(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We obtain\n\\[\n  E = mc^2 \\,.\n\\]\n",
        encoding="utf-8",
    )
    assert check(root) == []


def test_colon_before_equation_environment(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The energy relation is:\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    prose_07 = [f for f in findings if f.rule_id == "PROSE-07"]
    assert len(prose_07) == 1
    assert prose_07[0].line == 1
    assert prose_07[0].column == 23


def test_colon_before_bracket_display_math(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We compute:\n\\[\n  a = b \\,.\n\\]\n",
        encoding="utf-8",
    )
    findings = check(root)
    prose_07 = [f for f in findings if f.rule_id == "PROSE-07"]
    assert len(prose_07) == 1
    assert prose_07[0].line == 1
    assert prose_07[0].column == 11


def test_colon_before_double_dollar_display_math(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We compute:\n$$\n  a = b \\,.\n$$\n",
        encoding="utf-8",
    )
    findings = check(root)
    prose_07 = [f for f in findings if f.rule_id == "PROSE-07"]
    assert len(prose_07) == 1
    assert prose_07[0].line == 1
    assert prose_07[0].column == 11


def test_colon_with_intervening_comment_and_whitespace(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The energy is: % note\n% another comment line\n\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    prose_07 = [f for f in findings if f.rule_id == "PROSE-07"]
    assert len(prose_07) == 1
    assert prose_07[0].line == 1
    assert prose_07[0].column == 14


def test_colon_earlier_in_paragraph_does_not_flag(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Note the following: in this context, the relation is\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert not any(f.rule_id == "PROSE-07" for f in findings)


def test_same_line_ignore_suppression_for_prose_07(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The energy relation is: % latex-lint:ignore=PROSE-07\n\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root)
    assert not any(f.rule_id == "PROSE-07" for f in findings)
