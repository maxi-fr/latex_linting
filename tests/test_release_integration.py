from pathlib import Path

import pytest

from latex_linting.cli import main as cli_main
from latex_linting.document import MissingIncludeError
from latex_linting.main import Finding, check
from latex_linting.rules.catalogue import RULES

ALL_RULE_IDS = frozenset(rule.rule_id for rule in RULES)


def _build_clean_thesis(tmp_path: Path) -> Path:
    """Build a multi-file thesis fixture that complies with all 36 rules."""
    root = tmp_path / "thesis.tex"
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    root.write_text(
        r"""\documentclass[12pt,twoside]{report}
\begin{document}
\input{chapters/chapter1.tex}
\input{chapters/chapter2.tex}
\end{document}
""",
        encoding="utf-8",
    )

    ch1 = chapters_dir / "chapter1.tex"
    ch1.write_text(
        r"""\chapter{Introduction to Neural Network Optimization}
\label{cha:introduction}
\section{Background and Context}
\label{sec:background}
This framework demonstrates efficient training procedures across distributed nodes.
We assume that the objective function is smooth and bounded.
Recent advances in deep learning provide solid foundations~\cite{ref:smith2020}.
The proposed technique is useful, e.\,g., when memory is constrained.
The \LaTeX{} formatting conventions are maintained throughout the document.
Evaluation was conducted over 10--20 epochs with a learning rate of $10\,\mathrm{kHz}$.
We obtain ``well-formed'' outputs under varying initial conditions.
The distinction is \emph{crucial} for numerical stability.

A separate paragraph describes the mathematical notation used in later sections.
The mass-energy relationship yields an equivalent expression
\begin{equation}
\label{eq:mass_energy}
  E = m \cdot c^2 \,.
\end{equation}
The parameter ratio is expressed as $a/b$ rather than a compound fraction.
Trigonometric projections evaluate $\sin(x)$ along with constant offset $3.14$.
We inspect Figure~\ref{fig:architecture} in Chapter~\ref{cha:introduction} for structural details.

\section{System Architecture}
\label{sec:architecture}
\subsection{Processing Pipeline}
\label{sec:pipeline}
The input stage filters ambient noise before vector quantization.

\subsection{Execution Engine}
\label{sec:engine}
The pipeline executes concurrently across GPU clusters.
\begin{figure}
  \centering
  \includegraphics{pipeline.png}
  \caption{Overview of the distributed pipeline architecture.}
  \label{fig:architecture}
\end{figure}
The diagram highlights all primary communication channels between nodes.
""",
        encoding="utf-8",
    )

    ch2 = chapters_dir / "chapter2.tex"
    ch2.write_text(
        r"""\chapter{Evaluation and Empirical Results}
\label{cha:evaluation}
\section{Experimental Benchmark Setup}
\label{sec:benchmark}
We evaluate the method described in Section~\ref{sec:background} under realistic workloads.
Recall the relation defined in~\eqref{eq:mass_energy}, which bounds maximum throughput.
As shown in Table~\ref{tab:results}, latency scales favorably with cluster size.

\begin{table}
  \centering
  \caption{Measured throughput and latency across configurations.}
  \label{tab:results}
  \begin{tabular}{lrr}
    \toprule
    Configuration & Throughput & Latency \\
    \midrule
    Baseline & 120 & 45 \\
    Distributed & 340 & 18 \\
    \bottomrule
  \end{tabular}
\end{table}
All benchmark measurements reflect ten repeated trials with minimal variance.

\section{Summary of Findings}
\label{sec:summary}
The findings confirm the efficiency of our distributed scheduling design.
""",
        encoding="utf-8",
    )

    return root


def _build_violating_thesis(tmp_path: Path) -> Path:
    """Build a multi-file thesis fixture containing violations of all 36 rules."""
    root = tmp_path / "thesis_violating.tex"
    chapters_dir = tmp_path / "chapters_violating"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    # WORK-03: forbidden option 'draft'
    root.write_text(
        r"""\documentclass[draft,12pt]{report}
\addbibresource{chapters_violating/violating.bib}
\begin{document}
\input{chapters_violating/ch_struc_prose.tex}
\input{chapters_violating/ch_math_fig_tab.tex}
\end{document}
""",
        encoding="utf-8",
    )

    # CITE-08: incomplete bibliography entry
    bib = chapters_dir / "violating.bib"
    bib.write_text(
        r"""@article{bad_article,
  author = {Author, A.},
  title = {Incomplete Article},
  year = {2020},
}
""",
        encoding="utf-8",
    )

    # Violations in first chapter:
    # PROSE-04: lowercase word at end: 'and'
    # PROSE-02: 'This demonstrates'
    # PROSE-03: ', that'
    # CITE-04: citation after period
    # TYPO-01: regular space before cite/ref
    # TYPO-02: 'Figure 1' without nonbreaking space
    # TYPO-03: 'e.g.' without thin space
    # TYPO-04: '\LaTeX is' swallowed space
    # TYPO-05: '10-20' hyphen range
    # TYPO-06: '"quotes"' straight quotes
    # TYPO-07: '\underline{underlined}'
    # TYPO-08: '\\' as paragraph break in running text
    # TYPO-10: reference without category noun
    # STRUC-02: '\subsubsection{Deep Heading}'
    # STRUC-03: isolated child (only 1 section in chapter, or only 1 subsection in section)
    # STRUC-06: section ending on equation/table/figure/list
    ch1 = chapters_dir / "ch_struc_prose.tex"
    ch1.write_text(
        r"""\chapter{Structure and Prose and}
\label{wrong_cha_prefix}
\section{Isolated Section With Violations}
\label{sec:isolated}
This demonstrates standalone demonstratives.
We observe, that commas before that are flagged.
Sentence terminal period.\cite{ref:bad_cite}
Reference without nonbreaking space \ref{sec:isolated}.
Fixed expression Figure 1 needs a tilde.
Abbreviation e.g. needs thin space.
The \LaTeX is swallowed.
Range 10-20 uses single hyphen.
Here are "straight quotes" in text.
Here is \underline{underlined text} in prose.
Line break command \\ used as paragraph break.

\subsubsection{Deep Heading Exceeding Subsection}
Text in deep heading.

\begin{equation}
  x = y \,.
\end{equation}
""",
        encoding="utf-8",
    )

    # Violations in second chapter:
    # PROSE-07: colon before displayed equation
    # MATH-01: missing terminal punctuation in display equation
    # MATH-02: unreferenced numbered equation
    # MATH-03: redundant 'equation \eqref{...}'
    # MATH-04: inline \frac{a}{b}
    # MATH-06: $10 kg$ number-unit
    # MATH-09: $a * b$ programming operator
    # MATH-12: $sin(x)$ un-upright function
    # MATH-13: blank line in display math
    # MATH-14: $3,14$ decimal comma
    # TYPO-11: forward reference to equation
    # FIG-03: unreferenced figure
    # FIG-06: caption without terminal dot
    # FIG-07: label before caption
    # FIG-08: \begin{center} in figure
    # TAB-01: vertical rules | and \hline
    # TAB-02: caption after tabular
    # TAB-03: \begin{center} in table
    # TYPO-09: bad prefix on label
    ch2 = chapters_dir / "ch_math_fig_tab.tex"
    ch2.write_text(
        r"""\chapter{Mathematical and Float Conventions}
\label{cha:math_floats}
\section{Math Violations}
\label{sec:math_violations}
We preview equation~\eqref{eq:referenced_formula} before introducing it.
\begin{equation}
\label{eq:strictly_unreferenced}
  E = m \cdot c^2 \,.
\end{equation}
We introduce the formula as:
\begin{equation}
\label{eq:referenced_formula}
  a = b

  c * d
\end{equation}
In running text we mention equation \eqref{eq:referenced_formula}.
Here is inline fraction $\frac{1}{2}$ and unit $10 kg$ and function $sin(x)$ and comma $3,14$.

\section{Float Violations}
\label{sec:float_violations}
\begin{figure}
  \begin{center}
    \label{fig:misordered}
    \includegraphics{pic.png}
    \caption{Figure caption without dot}
  \end{center}
\end{figure}

\begin{table}
  \begin{center}
    \begin{tabular}{|l|r|}
      \hline
      Item & Count \\
      \hline
      A & 1 \\
      \hline
    \end{tabular}
    \caption{Table caption below tabular.}
    \label{tab:misplaced}
  \end{center}
\end{table}
Ending text to prevent STRUC-06 in this section.
""",
        encoding="utf-8",
    )

    return root


def test_clean_multi_file_thesis(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _build_clean_thesis(tmp_path)

    # API check produces no findings
    findings = check(root)
    assert findings == []

    # CLI check exits 0 with no stdout and no stderr
    exit_code = cli_main(["check", str(root)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_violating_multi_file_thesis_covers_all_rules(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _build_violating_thesis(tmp_path)

    findings = check(root)
    reported_rule_ids = {f.rule_id for f in findings}

    # Verify all 36 rules are triggered
    missing_rules = ALL_RULE_IDS - reported_rule_ids
    assert not missing_rules, f"Rules not triggered in violating fixture: {missing_rules}"

    # CLI check returns exit code 1
    exit_code = cli_main(["check", str(root)])
    assert exit_code == 1

    captured = capsys.readouterr()
    assert captured.err == ""

    # CLI stdout must contain every finding reported by API
    for finding in findings:
        expected_line = f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id} {finding.explanation}"
        assert expected_line in captured.out
        assert finding.excerpt in captured.out


def test_suppression_directives_multi_rule_and_isolation(tmp_path: Path) -> None:
    root = tmp_path / "root_suppr.tex"
    inc = tmp_path / "inc_suppr.tex"

    # Multi-rule same-line ignore
    root.write_text(
        r"""\documentclass{report}
\begin{document}
$\frac{1}{2}$ and $sin(x)$ % latex-lint: ignore=MATH-04, MATH-12
$\frac{3}{4}$ and \underline{text} % latex-lint: ignore=MATH-04
\input{inc_suppr.tex}
\end{document}
""",
        encoding="utf-8",
    )

    # File-local disable and German passage exclusion in included file
    inc.write_text(
        r"""% latex-lint: disable=MATH-04, TYPO-07
$\frac{5}{6}$ and \underline{German text}
% latex-lint: enable=MATH-04
$\frac{7}{8}$ and \underline{still disabled text}
""",
        encoding="utf-8",
    )

    findings = check(root)
    # Line 3: MATH-04 and MATH-12 both ignored -> 0 findings on line 3
    # Line 4: MATH-04 ignored, but TYPO-07 is active -> TYPO-07 finding on line 4
    # inc line 2: MATH-04 and TYPO-07 disabled -> 0 findings
    # inc line 4: MATH-04 re-enabled -> MATH-04 reported; TYPO-07 still disabled -> TYPO-07 not reported
    root_findings = [f for f in findings if Path(f.filename).name == "root_suppr.tex"]
    inc_findings = [f for f in findings if Path(f.filename).name == "inc_suppr.tex"]

    assert len(root_findings) == 1
    assert root_findings[0].rule_id == "TYPO-07"
    assert root_findings[0].line == 4

    assert len(inc_findings) == 1
    assert inc_findings[0].rule_id == "MATH-04"
    assert inc_findings[0].line == 4


def test_invocation_wide_exclusions_api_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "single.tex"
    root.write_text(
        r"""\documentclass{report}
\begin{document}
$\frac{1}{2}$ and $a * b$ and "quote"
\end{document}
""",
        encoding="utf-8",
    )

    # API with ignored_rules
    findings_all = check(root)
    assert {f.rule_id for f in findings_all} == {"MATH-04", "MATH-09", "TYPO-06"}

    findings_filtered = check(root, ignored_rules=["MATH-04", "TYPO-06"])
    assert {f.rule_id for f in findings_filtered} == {"MATH-09"}

    # CLI with --ignore
    exit_code = cli_main(["check", "--ignore", "MATH-04, TYPO-06", str(root)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "MATH-09" in captured.out
    assert "MATH-04" not in captured.out
    assert "TYPO-06" not in captured.out

    # CLI with all rules ignored -> exit code 0
    exit_code_clean = cli_main(["check", "--ignore", "MATH-04,MATH-09,TYPO-06", str(root)])
    assert exit_code_clean == 0
    captured_clean = capsys.readouterr()
    assert captured_clean.out == ""


def test_cross_file_references_resolve_correctly(tmp_path: Path) -> None:
    root = tmp_path / "cross_root.tex"
    ch1 = tmp_path / "ch1.tex"
    ch2 = tmp_path / "ch2.tex"

    root.write_text(
        r"""\documentclass{report}
\begin{document}
\input{ch1.tex}
\input{ch2.tex}
\end{document}
""",
        encoding="utf-8",
    )

    # Equation in ch1
    ch1.write_text(
        r"""\chapter{First}
\begin{equation}
\label{eq:shared_model}
  y = x \,.
\end{equation}
Text continuation after equation.
""",
        encoding="utf-8",
    )

    # Referenced in ch2
    ch2.write_text(
        r"""\chapter{Second}
We use the model from \eqref{eq:shared_model}.
""",
        encoding="utf-8",
    )

    findings = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert findings == []

    # Now remove reference from ch2 -> MATH-02 should flag eq:shared_model in ch1
    ch2.write_text(
        r"""\chapter{Second}
No reference here.
""",
        encoding="utf-8",
    )

    findings_unreferenced = [f for f in check(root) if f.rule_id == "MATH-02"]
    assert len(findings_unreferenced) == 1
    assert Path(findings_unreferenced[0].filename).name == "ch1.tex"
    assert findings_unreferenced[0].line == 3


def test_source_positions_preserved(tmp_path: Path) -> None:
    root = tmp_path / "pos_root.tex"
    sub = tmp_path / "sub.tex"

    root.write_text(
        r"""\documentclass{report}
Intro.
\input{sub.tex}
""",
        encoding="utf-8",
    )

    sub.write_text(
        "Line one.\nLine two with $\\frac{x}{y}$.\n",
        encoding="utf-8",
    )

    findings = check(root)
    math_findings = [f for f in findings if f.rule_id == "MATH-04"]
    assert len(math_findings) == 1
    f = math_findings[0]
    assert Path(f.filename).name == "sub.tex"
    assert f.line == 2
    assert f.column == 16
    assert f.excerpt == r"Line two with $\frac{x}{y}$."


def test_missing_input_and_invalid_rules_api_and_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # 1. Missing root file
    missing_root = tmp_path / "does_not_exist.tex"
    with pytest.raises(FileNotFoundError):
        check(missing_root)
    assert cli_main(["check", str(missing_root)]) == 2
    err = capsys.readouterr().err
    assert "latex-lint:" in err

    # 2. Missing included file
    root_broken_include = tmp_path / "broken_inc.tex"
    root_broken_include.write_text(r"\input{missing_file.tex}", encoding="utf-8")
    with pytest.raises(MissingIncludeError):
        check(root_broken_include)
    assert cli_main(["check", str(root_broken_include)]) == 2
    err = capsys.readouterr().err
    assert "missing_file.tex" in err

    # 3. Unknown rule in ignored_rules
    valid_file = tmp_path / "valid.tex"
    valid_file.write_text(r"Plain text.", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown rule ID"):
        check(valid_file, ignored_rules=["NONEXISTENT-99"])
    assert cli_main(["check", "--ignore", "NONEXISTENT-99", str(valid_file)]) == 2
    err = capsys.readouterr().err
    assert "unknown rule ID" in err

    # 4. Unknown rule in in-source directive
    bad_directive_file = tmp_path / "bad_dir.tex"
    bad_directive_file.write_text(r"% latex-lint: ignore=UNKNOWN-RULE" + "\nText.", encoding="utf-8")
    with pytest.raises(ValueError, match="unknown rule ID"):
        check(bad_directive_file)
    assert cli_main(["check", str(bad_directive_file)]) == 2
    err = capsys.readouterr().err
    assert "unknown rule ID" in err

    # 5. CLI rule command
    assert cli_main(["rule", "MATH-04"]) == 0
    out = capsys.readouterr().out
    assert "MATH-04:" in out
    assert "Passing examples:" in out

    with pytest.raises(SystemExit) as exc_info:
        cli_main(["rule", "UNKNOWN-RULE"])
    assert exc_info.value.code == 2
