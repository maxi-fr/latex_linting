from pathlib import Path

from latex_linting.main import check


def test_valid_bare_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As seen in \\eqref{eq:foo}, the error decreases.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_valid_sentence_start_equation_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Equation~\\eqref{eq:foo} describes the system dynamics.\nEquation \\eqref{eq:bar} is also valid.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_valid_sentence_start_equation_ref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Equation~\\ref{eq:foo} describes the system dynamics.\nEquation \\ref{eq:bar} is also valid.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_valid_sentence_start_after_period(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "The derivation is complete. Equation~\\eqref{eq:foo} establishes the bound.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_valid_sentence_start_german(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Gleichung~\\eqref{eq:foo} beschreibt das System.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_valid_section_and_figure_refs(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "See Section~\\ref{sec:methods} and Figure~\\ref{fig:arch} for details.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_mid_sentence_redundant_equation_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We observe this in equation~\\eqref{eq:foo}.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"
    assert findings[0].line == 1
    assert findings[0].column == 20
    assert "equation~\\eqref{eq:foo}" in findings[0].excerpt


def test_mid_sentence_redundant_capitalized_equation_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We observe that in Equation~\\eqref{eq:foo}, the error increases.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"
    assert findings[0].column == 20


def test_mid_sentence_redundant_eq_dot_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As given in Eq.~\\eqref{eq:foo}, the parameter is fixed.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"
    assert findings[0].column == 13


def test_mid_sentence_redundant_eq_dot_lowercase_eqref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As given in eq.~\\eqref{eq:foo}, the parameter is fixed.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"


def test_mid_sentence_redundant_german_gleichung(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Wie in Gleichung~\\eqref{eq:foo} dargestellt, gilt dies.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"


def test_mid_sentence_redundant_german_gl_dot(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "Wie in Gl.~\\eqref{eq:foo} dargestellt, gilt dies.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"


def test_abbreviation_before_equation_not_sentence_start(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "This applies, i.e. Equation~\\eqref{eq:foo} states the rule.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"


def test_ref_used_for_equation(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As seen in \\ref{eq:foo}, the result holds.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"
    assert findings[0].line == 1
    assert findings[0].column == 12


def test_parentheses_around_ref(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "As seen in (\\ref{eq:foo}), the result holds.\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert len(findings) == 1
    assert findings[0].rule_id == "MATH-03"


def test_comment_and_verbatim_excluded(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% As seen in equation~\\eqref{eq:foo}\n\\begin{verbatim}\nin equation \\eqref{eq:foo}\n\\end{verbatim}\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We note that equation~\\eqref{eq:foo} holds. % latex-lint:ignore=MATH-03\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_disable_enable_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "% latex-lint:disable=MATH-03\nWe note that equation~\\eqref{eq:foo} holds.\n% latex-lint:enable=MATH-03\n",
        encoding="utf-8",
    )
    findings = [f for f in check(root) if f.rule_id == "MATH-03"]
    assert findings == []


def test_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(
        "We note that equation~\\eqref{eq:foo} holds.\n",
        encoding="utf-8",
    )
    findings = check(root, ignored_rules=["MATH-03"])
    assert not any(f.rule_id == "MATH-03" for f in findings)
