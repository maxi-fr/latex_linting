from pathlib import Path

import pytest

from latex_linting.main import check


def test_valid_referenced_equation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:einstein}\n\\end{equation}\n"
        "As seen in \\eqref{eq:einstein}, mass and energy are equivalent.\n",
        encoding="utf-8",
    )
    assert check(root) == []


@pytest.mark.parametrize("ref_cmd", [r"\ref", r"\autoref", r"\cref", r"\Cref"])
def test_valid_referenced_with_other_commands(tmp_path: Path, ref_cmd: str) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        f"\\begin{{equation}}\n  E = mc^2 \\,.\n  \\label{{eq:einstein}}\n\\end{{equation}}\n"
        f"See {ref_cmd}{{eq:einstein}} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_valid_multiple_references_in_cref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  a = b \\,.\n  \\label{eq:first}\n\\end{equation}\n"
        "\\begin{equation}\n  c = d \\,.\n  \\label{eq:second}\n\\end{equation}\n"
        "See \\cref{eq:first, eq:second} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


@pytest.mark.parametrize(
    "env",
    [
        "equation*",
        "align*",
        "gather*",
        "multline*",
        "alignat*",
        "flalign*",
        "eqnarray*",
    ],
)
def test_valid_unnumbered_environments(tmp_path: Path, env: str) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        f"\\begin{{{env}}}\n  E = mc^2 \\,.\n\\end{{{env}}}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_valid_bracket_and_dollar_display_math(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\[\n  x = y \\,.\n\\]\n$$\n  a = b \\,.\n$$\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_unreferenced_labeled_equation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-02"
    assert findings[0].line == 3
    assert findings[0].column == 3
    assert "\\label{eq:unused}" in findings[0].excerpt


def test_unlabeled_numbered_equation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_unlabeled_numbered_align(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{align}\n  a &= b \\,.\n\\end{align}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_multiline_align_partially_referenced(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{align}\n"
        "  a &= b \\label{eq:used} \\\\\n"
        "  c &= d \\label{eq:unused} \\,.\n"
        "\\end{align}\n"
        "As seen in \\eqref{eq:used}, this holds.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-02"
    assert findings[0].line == 3
    assert "eq:unused" in findings[0].excerpt


def test_cross_file_reference_child_references_parent(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    child = tmp_path / "chapter1.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:mass_energy}\n\\end{equation}\n\\input{chapter1.tex}\n",
        encoding="utf-8",
    )
    child.write_text(
        "In this chapter we apply \\eqref{eq:mass_energy}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_cross_file_reference_parent_references_child(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    child = tmp_path / "chapter1.tex"
    root.write_text(
        "We will use \\eqref{eq:future_eq}.\n\\input{chapter1.tex}\n",
        encoding="utf-8",
    )
    child.write_text(
        "\\begin{equation}\n  F = ma \\,.\n  \\label{eq:future_eq}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_forward_reference_in_same_file(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Before stating the law, we foreshadow \\eqref{eq:law}.\n"
        "\\begin{equation}\n  v = u + at \\,.\n  \\label{eq:law}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_reference_in_comment_does_not_count(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}\n"
        "% As seen in \\eqref{eq:unused}, this was commented out.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-02"


def test_reference_in_verbatim_does_not_count(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}\n"
        "\\begin{verbatim}\n\\eqref{eq:unused}\n\\end{verbatim}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-02"


def test_label_in_comment_does_not_count(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n% \\label{eq:foo}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_same_line_suppression_on_label(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused} % latex-lint:ignore=MATH-02\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=MATH-02\n"
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}\n"
        "% latex-lint:enable=MATH-02\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["MATH-02"])
    assert not any(f.rule_id == "MATH-02" for f in findings)
