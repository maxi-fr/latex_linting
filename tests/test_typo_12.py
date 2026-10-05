from pathlib import Path

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_typo_12_metadata() -> None:
    """Verify rule ID, limits, examples, and description of TYPO-12."""
    rule = get_rule("TYPO-12")
    assert rule.rule_id == "TYPO-12"
    assert "acro" in rule.explanation.lower()
    assert "\\DeclareAcronym" in rule.explanation
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "acronym" in rule.limits.lower()


def test_valid_acro_usage(tmp_path: Path) -> None:
    """Pass valid acronym declarations and references via acro commands."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\DeclareAcronym{mpc}{\n"
        "  short = MPC,\n"
        "  long = Model Predictive Control\n"
        "}\n"
        "\\DeclareAcronym{svm}{\n"
        "  short = {SVM},\n"
        "  long = {Support Vector Machine}\n"
        "}\n"
        "We evaluate \\ac{mpc} against \\ac{svm}.\n"
        "Subsequently, \\acs{mpc} and \\acl{svm} perform reliably.\n"
        "Plural \\acp{mpc} are also evaluated.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert findings == []


def test_valid_exempt_terms_pass(tmp_path: Path) -> None:
    """Pass Roman numerals and universal terms in parentheses."""
    root = tmp_path / "thesis.tex"
    source = (
        "We verify conditions (II) and (IV) in stage (VI).\n"
        "Results are exported to portable document format (PDF).\n"
        "Documentation is accessible via (URL) and standard (IEEE).\n"
        "Genetic sequences (DNA) and (RNA) are analyzed.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert findings == []


def test_invalid_manual_introduction_undeclared(tmp_path: Path) -> None:
    """Detect manual acronym introductions in parentheses without acro."""
    root = tmp_path / "thesis.tex"
    source = (
        "We evaluate Model Predictive Control (MPC) on the benchmark.\n"
        "This is paired with Gaussian process (GP) regression.\n"
        "We monitor State of Charge (SoC) and Degrees of Freedom (DoF).\n"
        "We employ Convolutional Neural Networks (CNNs) as classifiers.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert len(findings) == 5
    assert all("Do not manually introduce acronym" in f.explanation for f in findings)
    assert findings[0].line == 1
    assert "MPC" in findings[0].excerpt
    assert findings[1].line == 2
    assert "GP" in findings[1].excerpt
    assert findings[2].line == 3
    assert "SoC" in findings[2].excerpt
    assert findings[3].line == 3
    assert "DoF" in findings[3].excerpt
    assert findings[4].line == 4
    assert "CNNs" in findings[4].excerpt


def test_invalid_manual_introduction_declared(tmp_path: Path) -> None:
    """Detect manual parentheses for an acronym that was declared in acro."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\n"
        "We introduce Model Predictive Control (MPC) here.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert len(findings) == 1
    assert "declared in acro" in findings[0].explanation
    assert "\\ac{mpc}" in findings[0].explanation


def test_invalid_bypassed_declared_acronym(tmp_path: Path) -> None:
    """Detect bare occurrences of declared acronym short forms in prose."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\n"
        "In this chapter, MPC is applied to the tracking problem.\n"
        "We also compare multiple MPCs.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert len(findings) == 2
    assert findings[0].line == 2
    assert "bare text" in findings[0].explanation
    assert findings[1].line == 3


def test_invalid_undefined_acronym_reference(tmp_path: Path) -> None:
    """Detect acro usage commands referencing keys that have not been declared."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\n"
        "We reference \\ac{mpc} correctly.\n"
        "However, \\ac{unknown_key} is not declared.\n"
        "Neither is \\acs{missing_item} nor \\acl{another_missing}.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert len(findings) == 3
    assert all("not declared with \\DeclareAcronym" in f.explanation for f in findings)
    assert findings[0].line == 3
    assert "unknown_key" in findings[0].explanation
    assert findings[1].line == 4
    assert "missing_item" in findings[1].explanation
    assert findings[2].line == 4
    assert "another_missing" in findings[2].explanation


def test_cross_file_acronym_resolution(tmp_path: Path) -> None:
    """Resolve acronym declarations across included child files."""
    root = tmp_path / "thesis.tex"
    macros = tmp_path / "macros.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"

    root.write_text(
        "\\input{macros.tex}\n\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    macros.write_text(
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        "We successfully use \\ac{mpc} here.\n",
        encoding="utf-8",
    )
    ch2.write_text(
        "In child file, bare MPC is used.\nAlso \\ac{undeclared} is referenced.\n",
        encoding="utf-8",
    )

    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert len(findings) == 2
    assert "ch2.tex" in findings[0].filename
    assert findings[0].line == 1
    assert "bare text" in findings[0].explanation
    assert findings[1].line == 2
    assert "undeclared" in findings[1].explanation


def test_math_comments_and_verbatim_excluded(tmp_path: Path) -> None:
    """Exclude math mode, comments, and literal blocks from acronym checks."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\n"
        "% In comment: Model Predictive Control (MPC) and bare MPC.\n"
        "In math mode: $(\\text{MPC}) = x$ and $MPC$.\n"
        "\\begin{verbatim}\n"
        "Code with (MPC) and bare MPC.\n"
        "\\end{verbatim}\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert findings == []


def test_same_line_suppression(tmp_path: Path) -> None:
    """Suppress TYPO-12 finding with inline comment directive."""
    root = tmp_path / "thesis.tex"
    source = (
        "We introduce Model Predictive Control (MPC) here. % latex-lint:ignore=TYPO-12\n"
        "We use bare \\ac{unknown} here. % latex-lint:ignore=TYPO-12\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id == "TYPO-12"]
    assert findings == []
