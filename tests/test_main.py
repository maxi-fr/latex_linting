from pathlib import Path

import pytest

from latex_linting.main import check
from latex_linting.rules.catalogue import RULES, get_rule


@pytest.mark.parametrize("source", [r"$\frac{a}{b}$", r"\(\frac{a}{b}\)", r"\begin{math}\frac{a}{b}\end{math}"])
def test_inline_fraction(source: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == "MATH-04"
    assert finding.filename == str(root)
    assert (finding.line, finding.column) == (1, source.index(r"\frac") + 1)
    assert finding.excerpt == source
    assert "inline" in finding.explanation
    assert "slash" in finding.correction
    assert root.read_text(encoding="utf-8") == source
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "source",
    [
        r"$a/b$ and $s^{-1}$",
        r"$$\frac{a}{b}$$",
        r"\[\frac{a}{b}\]",
        r"\begin{equation}\frac{a}{b}\end{equation}",
        r"\begin{align*}x &= \frac{a}{b}\end{align*}",
        "% $\\frac{a}{b}$\nPlain text.",
        r"\verb|$\frac{a}{b}$|",
        r"\verb*+$\frac{a}{b}$+",
        r"\begin{verbatim}$\frac{a}{b}$\end{verbatim}",
        r"\begin{verbatim*}$\frac{a}{b}$\end{verbatim*}",
        r"\begin{lstlisting}$\frac{a}{b}$\end{lstlisting}",
        r"\begin{minted}{latex}$\frac{a}{b}$\end{minted}",
        r"\$\frac{a}{b}\$",
        r"$\fraction{a}{b} + \dfrac{a}{b} + \tfrac{a}{b}$",
        r"\frac{a}{b}",
    ],
)
def test_valid_or_excluded_source(source: str, tmp_path: Path) -> None:
    root = tmp_path / "thesis.tex"
    root.write_text(source, encoding="utf-8")
    assert check(root) == []


def test_nested_multiline_positions_and_order(tmp_path: Path) -> None:
    root = tmp_path / "nested.tex"
    source = "Intro.\n$\\frac{a + {b}}{\n  \\frac{c}{d}}$ and \\(\\frac{e}{f}\\)\n"
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [(item.line, item.column) for item in findings] == [(2, 2), (3, 3), (3, 23)]
    assert findings[1].excerpt == source.splitlines()[2]
    assert findings == check(root)


def test_comments_escapes_and_literals_preserve_context(tmp_path: Path) -> None:
    root = tmp_path / "contexts.tex"
    source = (
        "$a \\% \\frac{1}{2} % $ \\frac{ignored}{ignored}\n"
        " + \\verb|$%\\frac{x}{y}| + \\frac{3}{4}$\n"
        "\\\\% $\\frac{ignored}{ignored}$\n"
        "\\begin{lstlisting}\n$%\\frac{ignored}{ignored}\n\\end{lstlisting}\n"
        "$\\frac{5}{6}$\n"
    )
    root.write_text(source, encoding="utf-8")
    findings = check(root)
    assert [(item.line, item.column) for item in findings] == [(1, 7), (2, 27), (7, 2)]


def test_rule_information() -> None:
    rule = get_rule("MATH-04")
    assert rule.rule_id == "MATH-04"
    assert "inline" in rule.explanation
    assert rule.passing_examples
    assert rule.failing_examples
    assert "macro" in rule.limits
    with pytest.raises(KeyError):
        get_rule("UNKNOWN")


def test_input_errors(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        check(tmp_path / "missing.tex")
    root = tmp_path / "invalid.tex"
    root.write_bytes(b"\xff")
    with pytest.raises(UnicodeError):
        check(root)


@pytest.mark.parametrize(
    "environment",
    [
        "displaymath",
        "equation",
        "equation*",
        "align",
        "align*",
        "alignat",
        "alignat*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "flalign",
        "flalign*",
        "eqnarray",
        "eqnarray*",
    ],
)
def test_display_environments_restore_context(environment: str, tmp_path: Path) -> None:
    root = tmp_path / "display.tex"
    root.write_text(
        rf"\begin{{{environment}}}\frac{{a}}{{b}}\end{{{environment}}}" + "\n$\\frac{a}{b}$",
        encoding="utf-8",
    )
    assert [(finding.line, finding.column) for finding in check(root)] == [(2, 2)]


@pytest.mark.parametrize(("opening", "closing"), [("$", "$"), (r"\(", r"\)"), (r"\begin{math}", r"\end{math}")])
def test_inline_context_ends(opening: str, closing: str, tmp_path: Path) -> None:
    root = tmp_path / "inline.tex"
    root.write_text(opening + r"\frac{a}{b}" + closing + r"\frac{outside}{math}", encoding="utf-8")
    assert len(check(root)) == 1


def test_unicode_crlf_and_relative_filename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    source = "First line.\r\n\t界 $\\frac{a}{b}$\r\n"
    Path("root.tex").write_bytes(source.encode("utf-8"))
    finding = check("root.tex")[0]
    assert finding.filename == "root.tex"
    assert (finding.line, finding.column) == (2, 5)
    assert finding.excerpt == "\t界 $\\frac{a}{b}$"
    assert Path("root.tex").read_bytes() == source.encode("utf-8")


def test_catalogue_examples_match_evaluation(tmp_path: Path) -> None:
    root = tmp_path / "example.tex"
    for rule in RULES:
        assert get_rule(rule.rule_id) is rule
        for example in rule.passing_examples:
            root.write_text(example, encoding="utf-8")
            assert check(root) == []
        for example in rule.failing_examples:
            root.write_text(example, encoding="utf-8")
            assert rule.rule_id in {finding.rule_id for finding in check(root)}


@pytest.mark.parametrize(
    "prefix",
    [
        r"$$\frac{a}{b}$$",
        r"\[\frac{a}{b}\]",
        r"\verb|$\frac{a}{b}$|",
        r"\verb*+$\frac{a}{b}$+",
        r"\begin{verbatim}$\frac{a}{b}$\end{verbatim}",
        r"\begin{verbatim*}$\frac{a}{b}$\end{verbatim*}",
        r"\begin{minted}{latex}$\frac{a}{b}$\end{minted}",
        r"\begin{lstlisting}$\frac{a}{b}$\end{lstlisting}",
        r"$\\frac{a}{b}$",
    ],
)
def test_context_transitions(prefix: str, tmp_path: Path) -> None:
    root = tmp_path / "transitions.tex"
    root.write_text(prefix + "\n$\\frac{a}{b}$", encoding="utf-8")
    assert [(finding.line, finding.column) for finding in check(root)] == [(2, 2)]
