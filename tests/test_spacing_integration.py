from pathlib import Path

from latex_linting.main import check


def test_multi_spacing_all_violations(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "As seen in Figure \\ref{sec:system}, results in Table 1 hold.\n"
        "Consider e.g. how \\LaTeX is used here.\n"
        "This section concludes with narrative prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TYPO-01" in rule_ids
    assert "TYPO-02" in rule_ids
    assert "TYPO-03" in rule_ids
    assert "TYPO-04" in rule_ids


def test_multi_spacing_targeted_same_line_suppression(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "As seen in Figure \\ref{sec:system}, results in Table 1 hold. % latex-lint:ignore=TYPO-01\n"
        "Consider e.g. how \\LaTeX is used here.\n"
        "This section concludes with narrative prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TYPO-01" not in rule_ids
    assert "TYPO-02" in rule_ids
    assert "TYPO-03" in rule_ids
    assert "TYPO-04" in rule_ids


def test_multi_spacing_invocation_wide_ignore(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "As seen in Figure \\ref{sec:system}, results in Table 1 hold.\n"
        "Consider e.g. how \\LaTeX is used here.\n"
        "This section concludes with narrative prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root, ignored_rules=["TYPO-01", "TYPO-03"])
    rule_ids = {f.rule_id for f in findings}
    assert "TYPO-01" not in rule_ids
    assert "TYPO-03" not in rule_ids
    assert "TYPO-02" in rule_ids
    assert "TYPO-04" in rule_ids


def test_multi_spacing_disable_enable(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "% latex-lint:disable=TYPO-02,TYPO-04\n"
        "As seen in Figure \\ref{sec:system}, results in Table 1 hold.\n"
        "Consider e.g. how \\LaTeX is used here.\n"
        "% latex-lint:enable=TYPO-02,TYPO-04\n"
        "This section concludes with narrative prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TYPO-01" in rule_ids
    assert "TYPO-02" not in rule_ids
    assert "TYPO-03" in rule_ids
    assert "TYPO-04" not in rule_ids


def test_multi_spacing_all_valid_forms(tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "As seen in Figure~\\ref{sec:system}, results in Table~1 hold.\n"
        "Consider, e.\\,g., how \\LaTeX{} is used here.\n"
        "The track is 3.5~km with 5\\,dB attenuation at 3~p.m.\n"
        "This section concludes with narrative prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id.startswith("TYPO-0")]
    assert findings == []
