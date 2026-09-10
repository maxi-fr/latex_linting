from pathlib import Path

from latex_linting.main import check


def test_ticket_12_multi_rule_all_violations(tmp_path: Path) -> None:
    """Detect violations of TYPO-05, TYPO-06, TYPO-07, and TYPO-08 in one document."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "\\label{sec:system}\n"
        "The sensor operates across 10-20 Hz with -5 dB sensitivity.\n"
        'We refer to this as the "baseline" configuration.\n'
        "We also \\underline{highlight} this crucial mode.\n"
        "The discussion continues on the next line.\\\\\n"
        "New paragraph follows.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    rule_ids = {f.rule_id for f in findings}
    assert "TYPO-05" in rule_ids
    assert "TYPO-06" in rule_ids
    assert "TYPO-07" in rule_ids
    assert "TYPO-08" in rule_ids


def test_ticket_12_multi_file_inclusion(tmp_path: Path) -> None:
    """Preserve rule findings and source tracking across included files."""
    root = tmp_path / "thesis.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"
    root.write_text(
        "\\section{Root}\n\\input{ch1.tex}\n\\input{ch2.tex}\n",
        encoding="utf-8",
    )
    ch1.write_text(
        '\\subsection{Chapter 1}\nRange 10-20 with offset -10.\nA "quote" here.\n',
        encoding="utf-8",
    )
    ch2.write_text(
        "\\subsection{Chapter 2}\nWe \\underline{underline} here.\nLine break follows.\\\\\nEnding prose.\n",
        encoding="utf-8",
    )
    findings = check(root)
    ch1_findings = [f for f in findings if "ch1.tex" in f.filename]
    ch2_findings = [f for f in findings if "ch2.tex" in f.filename]
    ch1_rules = {f.rule_id for f in ch1_findings}
    ch2_rules = {f.rule_id for f in ch2_findings}
    assert "TYPO-05" in ch1_rules
    assert "TYPO-06" in ch1_rules
    assert "TYPO-07" in ch2_rules
    assert "TYPO-08" in ch2_rules


def test_ticket_12_targeted_same_line_suppression(tmp_path: Path) -> None:
    """Suppress individual ticket 12 rules on matching lines."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "Range 10-20 % latex-lint:ignore=TYPO-05\n"
        'Text with "quote". % latex-lint:ignore=TYPO-06\n'
        "Text with \\underline{underline}. % latex-lint:ignore=TYPO-07\n"
        "Text with break.\\\\ % latex-lint:ignore=TYPO-08\n"
        "Ending prose.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id in {"TYPO-05", "TYPO-06", "TYPO-07", "TYPO-08"}]
    assert findings == []


def test_ticket_12_disable_enable_isolation(tmp_path: Path) -> None:
    """Respect disable/enable scope within a file without leaking to other files."""
    root = tmp_path / "thesis.tex"
    inc = tmp_path / "inc.tex"
    root.write_text(
        "\\section{Root}\n"
        "% latex-lint:disable=TYPO-05,TYPO-06,TYPO-07,TYPO-08\n"
        'Range 10-20 with "quote" and \\underline{text}.\\\\\n'
        "\\input{inc.tex}\n"
        "Still disabled: 10-20.\n"
        "% latex-lint:enable=TYPO-05,TYPO-06,TYPO-07,TYPO-08\n"
        "Re-enabled: 10-20.\n",
        encoding="utf-8",
    )
    inc.write_text(
        "\\subsection{Included}\nIn child, rule is active: 10-20.\n",
        encoding="utf-8",
    )
    findings = check(root)
    inc_findings = [f for f in findings if "inc.tex" in f.filename and f.rule_id == "TYPO-05"]
    root_findings = [f for f in findings if "thesis.tex" in f.filename and f.rule_id == "TYPO-05"]
    assert len(inc_findings) == 1
    assert len(root_findings) == 1
    assert root_findings[0].line == 7


def test_ticket_12_all_valid_forms(tmp_path: Path) -> None:
    """Pass all valid counterparts of ticket 12 rules without findings."""
    root = tmp_path / "thesis.tex"
    source = (
        "\\section{System Overview}\n"
        "The sensor operates across 10--20~Hz with $-5$~dB sensitivity.\n"
        "We develop a state-of-the-art closed-loop controller.\n"
        "We refer to this as the ``baseline'' configuration with \\enquote{verified} data.\n"
        "It's the author's work with students' measurements.\n"
        "We \\emph{emphasize} this mode and use \\textit{italics}.\n"
        "\\begin{tabular}{ll}\n"
        "\\textbf{Header 1} & \\textbf{Header 2} \\\\\n"
        "10 & 20 \\\\\n"
        "\\end{tabular}\n"
        "\\begin{align}\n"
        "x &= 1 \\\\\n"
        "y &= 2\n"
        "\\end{align}\n"
        "\\title{Thesis Title \\\\ Subtitle}\n"
        "\\author{Author Name \\\\ Department}\n"
        "\n"
        "New paragraph started with a blank line.\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = [f for f in check(root) if f.rule_id in {"TYPO-05", "TYPO-06", "TYPO-07", "TYPO-08"}]
    assert findings == []
