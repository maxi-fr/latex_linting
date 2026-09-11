from pathlib import Path

import pytest

from latex_linting.document import MissingIncludeError
from latex_linting.main import check


def test_basic_input_and_include(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    sub1 = tmp_path / "sub1.tex"
    sub2 = tmp_path / "sub2.tex"

    sub1.write_text("$\\frac{1}{2}$\n", encoding="utf-8")
    sub2.write_text("$\\frac{3}{4}$\n", encoding="utf-8")
    root.write_text("\\input{sub1.tex}\n\\include{sub2.tex}\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 2
    assert findings[0].filename == str(sub1)
    assert (findings[0].line, findings[0].column) == (1, 2)
    assert findings[0].excerpt == "$\\frac{1}{2}$"

    assert findings[1].filename == str(sub2)
    assert (findings[1].line, findings[1].column) == (1, 2)
    assert findings[1].excerpt == "$\\frac{3}{4}$"


def test_nested_includes_preserve_order(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    ch1_dir = tmp_path / "ch1"
    ch1_dir.mkdir()
    ch1 = ch1_dir / "chap.tex"
    sec = ch1_dir / "sec.tex"

    root.write_text("$\\frac{0}{1}$\n\\input{ch1/chap.tex}\n$\\frac{4}{5}$\n", encoding="utf-8")
    ch1.write_text("$\\frac{1}{2}$\n\\input{sec.tex}\n", encoding="utf-8")
    sec.write_text("$\\frac{2}{3}$\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 4
    assert [f.filename for f in findings] == [str(root), str(ch1), str(sec), str(root)]
    assert [(f.line, f.column) for f in findings] == [(1, 2), (1, 2), (1, 2), (3, 2)]


def test_omitted_tex_extension(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    sub = tmp_path / "sub.tex"
    sub.write_text("$\\frac{a}{b}$\n", encoding="utf-8")
    root.write_text("\\input{sub}\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 1
    assert findings[0].filename == str(sub)


def test_relative_path_resolution_file_and_root(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    ch1 = chapters / "ch1.tex"
    sec1 = chapters / "sec1.tex"
    common = tmp_path / "common.tex"

    root.write_text("\\input{chapters/ch1.tex}\n", encoding="utf-8")
    # sec1 is relative to ch1 directory, common is relative to root directory
    ch1.write_text("\\input{sec1}\n\\input{common}\n", encoding="utf-8")
    sec1.write_text("$\\frac{1}{2}$\n", encoding="utf-8")
    common.write_text("$\\frac{3}{4}$\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 2
    assert [f.filename for f in findings] == [str(sec1), str(common)]


def test_dynamic_macro_target_unsupported(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    root.write_text("\\input{\\mychapter}\n", encoding="utf-8")

    with pytest.raises(MissingIncludeError) as exc_info:
        check(root)
    assert exc_info.value.line == 1
    assert exc_info.value.target == "\\mychapter"
    assert "\\mychapter" in str(exc_info.value)


def test_comments_and_literals_do_not_include(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    root.write_text(
        "% \\input{missing.tex}\n"
        "\\begin{verbatim}\n\\input{missing.tex}\n\\end{verbatim}\n"
        "\\verb|\\input{missing.tex}|\n"
        "\\begin{lstlisting}\n\\include{missing.tex}\n\\end{lstlisting}\n"
        "$\\frac{a}{b}$\n",
        encoding="utf-8",
    )

    findings = check(root)
    assert len(findings) == 1
    assert findings[0].line == 9


def test_missing_included_file_raises_error(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    root.write_text("First line\n\\input{chapters/missing.tex}\n", encoding="utf-8")

    with pytest.raises(MissingIncludeError) as exc_info:
        check(root)

    assert exc_info.value.filename == str(root)
    assert exc_info.value.line == 2
    assert exc_info.value.target == "chapters/missing.tex"
    assert f"{root}:2: cannot find included file 'chapters/missing.tex'" == str(exc_info.value)


def test_suppression_isolation_parent_to_child(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    child = tmp_path / "child.tex"

    child.write_text("$\\frac{a}{b}$\n", encoding="utf-8")
    root.write_text("% latex-lint:disable=MATH-04\n\\input{child.tex}\n", encoding="utf-8")

    findings = [f for f in check(root) if f.rule_id == "MATH-04"]
    assert len(findings) == 1
    assert findings[0].filename == str(child)


def test_suppression_isolation_child_to_parent(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    child = tmp_path / "child.tex"

    child.write_text("% latex-lint:disable=MATH-04\n$\\frac{1}{2}$\n", encoding="utf-8")
    root.write_text("\\input{child.tex}\n$\\frac{a}{b}$\n", encoding="utf-8")

    findings = check(root)
    assert len(findings) == 1
    assert findings[0].filename == str(root)
    assert findings[0].line == 2


def test_suppression_isolation_child_enable_does_not_affect_parent(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    child = tmp_path / "child.tex"

    child.write_text("% latex-lint:enable=MATH-04\n$\\frac{1}{2}$\n", encoding="utf-8")
    root.write_text(
        "% latex-lint:disable=MATH-04\n\\input{child.tex}\n$\\frac{a}{b}$\n",
        encoding="utf-8",
    )

    findings = [f for f in check(root) if f.rule_id == "MATH-04"]
    assert len(findings) == 1
    assert findings[0].filename == str(child)


def test_invocation_wide_ignore_affects_all_sources(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    child = tmp_path / "child.tex"

    child.write_text("$\\frac{1}{2}$\n", encoding="utf-8")
    root.write_text("$\\frac{a}{b}$\n\\input{child.tex}\n", encoding="utf-8")

    assert check(root, ignored_rules=["MATH-04"]) == []


def test_unknown_rule_id_in_included_file_raises_error(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    child = tmp_path / "child.tex"

    child.write_text("% latex-lint:ignore=UNKNOWN-99\n$\\frac{1}{2}$\n", encoding="utf-8")
    root.write_text("\\input{child.tex}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="UNKNOWN-99"):
        check(root)


def test_circular_include_detected(tmp_path: Path) -> None:
    a = tmp_path / "a.tex"
    b = tmp_path / "b.tex"

    a.write_text("Line 1\n\\input{b.tex}\n", encoding="utf-8")
    b.write_text("Line 1\n\\input{a.tex}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="circular"):
        check(a)


def test_deterministic_ordering_repeated_runs(tmp_path: Path) -> None:
    root = tmp_path / "root.tex"
    sub1 = tmp_path / "sub1.tex"
    sub2 = tmp_path / "sub2.tex"

    root.write_text("$\\frac{1}{2}$\n\\input{sub1.tex}\n\\input{sub2.tex}\n", encoding="utf-8")
    sub1.write_text("$\\frac{3}{4}$\n$\\frac{5}{6}$\n", encoding="utf-8")
    sub2.write_text("$\\frac{7}{8}$\n", encoding="utf-8")

    first_run = check(root)
    second_run = check(root)
    assert first_run == second_run
