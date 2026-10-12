from pathlib import Path

import pytest

from latex_linting.cli import main
from latex_linting.formatter import format_files, format_latex


def test_format_basic_two_sentences() -> None:
    source = "First sentence. Second sentence."
    expected = "First sentence.\nSecond sentence."
    assert format_latex(source) == expected


def test_format_exclamation_and_question() -> None:
    source = "Is this true? Yes! Really? Certainly."
    expected = "Is this true?\nYes!\nReally?\nCertainly."
    assert format_latex(source) == expected


def test_format_combine_intra_sentence_linebreaks() -> None:
    source = "First sentence\nwrapped across lines. Second sentence."
    expected = "First sentence wrapped across lines.\nSecond sentence."
    assert format_latex(source) == expected


def test_format_idempotent() -> None:
    source = "First sentence.\nSecond sentence.\nThird sentence.\n"
    assert format_latex(source) == source


def test_format_preserve_indentation() -> None:
    source = "    \\item First sentence. Second sentence."
    expected = "    \\item First sentence.\n    Second sentence."
    assert format_latex(source) == expected


def test_format_preserve_indentation_multiple_sentences() -> None:
    source = "  Sentence one. Sentence two. Sentence three."
    expected = "  Sentence one.\n  Sentence two.\n  Sentence three."
    assert format_latex(source) == expected


def test_format_preserve_paragraph_breaks() -> None:
    source = "First sentence.\n\nSecond sentence."
    assert format_latex(source) == source


def test_format_abbreviations_not_split() -> None:
    source = (
        "As shown by Smith et al. in Fig. 1 and Tab. 2, the result is valid (cf. Sec. 3). "
        "This confirms the theory, e.g. under standard conditions."
    )
    expected = (
        "As shown by Smith et al. in Fig.~1 and Tab.~2, the result is valid (cf. Sec.~3).\n"
        "This confirms the theory, e.\\,g. under standard conditions."
    )
    assert format_latex(source) == expected


def test_format_german_abbreviations_not_split() -> None:
    source = "Das ist z. B. ein Test (d. h. eine Demonstration). Zweiter Satz folgt."
    expected = "Das ist z. B. ein Test (d. h. eine Demonstration).\nZweiter Satz folgt."
    assert format_latex(source) == expected


def test_format_initials_not_split() -> None:
    source = "A. Einstein and J. K. Rowling wrote this. Next sentence."
    expected = "A. Einstein and J. K. Rowling wrote this.\nNext sentence."
    assert format_latex(source) == expected


def test_format_decimal_numbers_not_split() -> None:
    source = "The ratio is 3.14 in test 1. Next sentence."
    expected = "The ratio is 3.14 in test 1.\nNext sentence."
    assert format_latex(source) == expected


def test_format_numbered_list_item_not_split() -> None:
    source = "1. First item sentence. Second item sentence."
    expected = "1. First item sentence.\nSecond item sentence."
    assert format_latex(source) == expected


def test_format_ellipsis_not_split() -> None:
    source = "Wait... not finished yet. Now it is."
    expected = "Wait... not finished yet.\nNow it is."
    assert format_latex(source) == expected


def test_format_comments_untouched() -> None:
    source = "% First sentence. Second sentence.\nProse here."
    assert format_latex(source) == source

    inline_comment = "First sentence. Second sentence. % A comment"
    expected = "First sentence.\nSecond sentence. % A comment"
    assert format_latex(inline_comment) == expected


def test_format_display_math_untouched() -> None:
    source = "\\begin{equation}\n  x = 1. % dot\n  y = 2.\n\\end{equation}\nNext sentence."
    assert format_latex(source) == source


def test_format_inline_math_preserved() -> None:
    source = "Let $x = 1.0$ and $y = 2.0$. Then $z = 3.0$ is the answer."
    expected = "Let $x = 1.0$ and $y = 2.0$.\nThen $z = 3.0$ is the answer."
    assert format_latex(source) == expected


def test_format_verbatim_untouched() -> None:
    source = "\\begin{verbatim}\nFirst sentence. Second sentence.\n\\end{verbatim}"
    assert format_latex(source) == source


def test_format_syntax_commands_arguments_untouched() -> None:
    source = "\\usepackage[version=1.0]{mhchem}\n\\section{1. Introduction}\nProse sentence. Another sentence."
    expected = "\\usepackage[version=1.0]{mhchem}\n\\section{1. Introduction}\nProse sentence.\nAnother sentence."
    assert format_latex(source) == expected


def test_format_citations_attached() -> None:
    source1 = "First sentence~\\cite{smith2020}. Second sentence."
    expected1 = "First sentence~\\cite{smith2020}.\nSecond sentence."
    assert format_latex(source1) == expected1

    source2 = "First sentence.\\cite{smith2020} Second sentence."
    expected2 = "First sentence.\\cite{smith2020}\nSecond sentence."
    assert format_latex(source2) == expected2


def test_format_footnotes() -> None:
    source = "First sentence.\\footnote{A note.} Second sentence."
    expected = "First sentence.\\footnote{A note.}\nSecond sentence."
    assert format_latex(source) == expected

    source_inner = "First sentence.\\footnote{Note one. Note two.} Second sentence."
    expected_inner = "First sentence.\\footnote{Note one.\nNote two.}\nSecond sentence."
    assert format_latex(source_inner) == expected_inner


def test_format_closing_quotes_and_brackets() -> None:
    source = "``First sentence.'' (Second sentence.) Third sentence."
    expected = "``First sentence.''\n(Second sentence.)\nThird sentence."
    assert format_latex(source) == expected


def test_format_files_in_place(tmp_path: Path) -> None:
    file1 = tmp_path / "doc1.tex"
    file2 = tmp_path / "doc2.tex"
    file1.write_text("Sentence one. Sentence two.", encoding="utf-8")
    file2.write_text("Sentence A. Sentence B.", encoding="utf-8")

    status = format_files([file1, file2])
    assert status == 0
    assert file1.read_text(encoding="utf-8") == "Sentence one.\nSentence two."
    assert file2.read_text(encoding="utf-8") == "Sentence A.\nSentence B."


def test_cli_format_command(tmp_path: Path) -> None:
    file1 = tmp_path / "thesis.tex"
    file1.write_text("First sentence. Second sentence.\n", encoding="utf-8")

    exit_code = main(["format", str(file1)])
    assert exit_code == 0
    assert file1.read_text(encoding="utf-8") == "First sentence.\nSecond sentence.\n"

    # Idempotent second run
    exit_code2 = main(["format", str(file1)])
    assert exit_code2 == 0
    assert file1.read_text(encoding="utf-8") == "First sentence.\nSecond sentence.\n"


def test_cli_format_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "nonexistent.tex"
    exit_code = main(["format", str(missing)])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "cannot find" in captured.err.lower() or "no such file" in captured.err.lower()


def test_caption_atomic_protects_multi_sentence_and_citations() -> None:
    source = (
        "\\caption{Parameters of the Jansen-Rit model. "
        "Values follow fit~\\cite{Jansen1995} and Yu et al.~\\cite{Yu2024}. "
        "The coupling factor is $K$.} % cite-checked: SUPPORTED\n"
    )
    assert format_latex(source) == source


def test_split_line_trailing_comment_relocation_for_citations() -> None:
    source = "Linear convergence was proved~\\cite{smith2020}. Later studies confirm this. % cite-checked: SUPPORTED"
    expected = "Linear convergence was proved~\\cite{smith2020}. % cite-checked: SUPPORTED\nLater studies confirm this."
    assert format_latex(source) == expected


def test_sentence_starter_lookahead() -> None:
    assert format_latex("We waited approx. 5 minutes.") == "We waited approx. 5 minutes."
    assert format_latex("Select the min. value.") == "Select the min. value."
    assert format_latex("Tested in vitro. however, failed.") == "Tested in vitro. however, failed."
    assert format_latex("Valid sentence. \\ref{sec:1} shows it.") == "Valid sentence.\n\\ref{sec:1} shows it."
    assert format_latex("Valid sentence. $x = 1$ is true.") == "Valid sentence.\n$x = 1$ is true."
    assert format_latex("Valid sentence. ``Quoted'' text.") == "Valid sentence.\n``Quoted'' text."


def test_name_initials_with_prepositions() -> None:
    source1 = "According to J. Smith, the method works. Next sentence."
    expected1 = "According to J. Smith, the method works.\nNext sentence."
    assert format_latex(source1) == expected1

    source2 = "From A. Einstein, we learn physics. Next sentence."
    expected2 = "From A. Einstein, we learn physics.\nNext sentence."
    assert format_latex(source2) == expected2

    source3 = "Sentence A. Sentence B."
    expected3 = "Sentence A.\nSentence B."
    assert format_latex(source3) == expected3


def test_academic_abbreviations_expanded() -> None:
    source = "Use def. 1 and thm. 2 (approx. 2 hrs., std. dev.). Next sentence."
    expected = "Use def. 1 and thm. 2 (approx. 2 hrs., std. dev.).\nNext sentence."
    assert format_latex(source) == expected


def test_numbered_lists_hierarchical_and_lettered() -> None:
    assert format_latex("1.1. Section Title. Next sentence.") == "1.1. Section Title.\nNext sentence."
    assert format_latex("a. First item sentence. Second sentence.") == "a. First item sentence.\nSecond sentence."
    assert format_latex("(1). First item. Second sentence.") == "(1). First item.\nSecond sentence."


def test_attached_label_and_index() -> None:
    source_label = "Sentence one.\\label{sec:one} Sentence two."
    expected_label = "Sentence one.\\label{sec:one}\nSentence two."
    assert format_latex(source_label) == expected_label

    source_index = "Sentence one.\\index{topic} Sentence two."
    expected_index = "Sentence one.\\index{topic}\nSentence two."
    assert format_latex(source_index) == expected_index


def test_escaped_braces_in_balanced_consumer() -> None:
    source = "Sentence with \\label{set:\\{a,b\\}} here. Second sentence."
    expected = "Sentence with \\label{set:\\{a,b\\}} here.\nSecond sentence."
    assert format_latex(source) == expected


def test_format_typo_01_reference_and_citation_ties() -> None:
    source = (
        "As seen in Figure \\ref{fig:arch} and Equation \\eqref{eq:1}.\n"
        "According to Smith \\cite{smith2020} and Jones \\citep{jones2021}.\n"
        "Broken across\n\\ref{fig:arch} line."
    )
    expected = (
        "As seen in Figure~\\ref{fig:arch} and Equation~\\eqref{eq:1}.\n"
        "According to Smith~\\cite{smith2020} and Jones~\\citep{jones2021}.\n"
        "Broken across~\\ref{fig:arch} line."
    )
    assert format_latex(source) == expected


def test_format_typo_01_sentence_boundaries_and_brackets_not_tied() -> None:
    source = "End of sentence. \\ref{fig:arch} begins new one.\nIn parenthesis (\\ref{fig:arch}) passes."
    expected = "End of sentence.\n\\ref{fig:arch} begins new one.\nIn parenthesis (\\ref{fig:arch}) passes."
    assert format_latex(source) == expected


def test_format_typo_02_fixed_expressions_and_units() -> None:
    source = (
        "In Figure 1, Table 2, Section 3, and Chapter 4.\n"
        "Dr. Müller and Prof. Smith attended at 3 p.m. or 10 Uhr.\n"
        "Values are 10 m, 5 kg, 20 s, 100 V, and 50 Hz."
    )
    expected = (
        "In Figure~1, Table~2, Section~3, and Chapter~4.\n"
        "Dr.~Müller and Prof.~Smith attended at 3~p.m. or 10~Uhr.\n"
        "Values are 10~m, 5~kg, 20~s, 100~V, and 50~Hz."
    )
    assert format_latex(source) == expected


def test_format_typo_03_abbreviations_thin_spaces() -> None:
    source = (
        "Consider, e.g., models and, i.e., conditions.\n"
        "Spaced e. g. and e.~g. are fixed.\n"
        "Sentence start: E.g., for example, and I.e., that is."
    )
    expected = (
        "Consider, e.\\,g., models and, i.\\,g., conditions.\n"
        "Spaced e.\\,g. and e.\\,g. are fixed.\n"
        "Sentence start: E.\\,g., for example, and I.\\,e., that is."
    )
    # Wait, i.e. has last letter 'e'
    source = "Consider, e.g., models and, i.e., conditions."
    expected = "Consider, e.\\,g., models and, i.\\,e., conditions."
    assert format_latex(source) == expected


def test_format_typo_04_parameterless_commands() -> None:
    source = "We use \\LaTeX for typing and \\BibTeX with \\TeX in code."
    expected = "We use \\LaTeX{} for typing and \\BibTeX{} with \\TeX{} in code."
    assert format_latex(source) == expected

    already_handled = "\\LaTeX{} is good and \\TeX\\ is too. Punctuation \\LaTeX."
    expected_already = "\\LaTeX{} is good and \\TeX\\ is too.\nPunctuation \\LaTeX."
    assert format_latex(already_handled) == expected_already


def test_format_typo_05_numeric_ranges_en_dash() -> None:
    source = "Values 10-20 on pp. 5-10, but not date 2026-10-11 or compound word state-of-the-art."
    expected = "Values 10--20 on pp.~5--10, but not date 2026-10-11 or compound word state-of-the-art."
    assert format_latex(source) == expected


def test_format_typo_06_quotes_and_apostrophes() -> None:
    source = (
        'This is "quoted" text and "results" vary.\n'
        "He stated: 'Results are preliminary.'\n"
        "Don't touch it's or students' data.\n"
        'Names include Schr\\"odinger and G\\"odel.'
    )
    expected = (
        "This is ``quoted'' text and ``results'' vary.\n"
        "He stated: `Results are preliminary.'\n"
        "Don't touch it's or students' data.\n"
        'Names include Schr\\"odinger and G\\"odel.'
    )
    assert format_latex(source) == expected


def test_format_whitespace_collapse_and_trim() -> None:
    source = "    Multiple   spaces   between   words.    Line two with trailing space.    \n"
    expected = "    Multiple spaces between words.\n    Line two with trailing space.\n"
    assert format_latex(source) == expected


def test_format_combine_multiline_sentence() -> None:
    source = "First sentence is split\nacross several lines\nand terminates here. Second sentence follows."
    expected = "First sentence is split across several lines and terminates here.\nSecond sentence follows."
    assert format_latex(source) == expected


def test_format_combine_item_wrapped_sentences() -> None:
    source = (
        "\\begin{itemize}\n"
        "    \\item First item\n"
        "    wrapped across lines.\n"
        "    \\item Second item sentence.\n"
        "\\end{itemize}"
    )
    expected = (
        "\\begin{itemize}\n"
        "    \\item First item wrapped across lines.\n"
        "    \\item Second item sentence.\n"
        "\\end{itemize}"
    )
    assert format_latex(source) == expected


def test_format_combine_with_citation_and_reference() -> None:
    source = "Linear convergence was proved by Smith\n\\cite{smith2020} in Section \\ref{sec:1}.\nNext sentence."
    expected = "Linear convergence was proved by Smith~\\cite{smith2020} in Section~\\ref{sec:1}.\nNext sentence."
    assert format_latex(source) == expected


def test_format_combine_preserves_comments() -> None:
    source = "First sentence % comment on line\nwrapped across lines.\n% Independent comment\nNext sentence."
    expected = "First sentence % comment on line\nwrapped across lines.\n% Independent comment\nNext sentence."
    assert format_latex(source) == expected


def test_format_combine_preserves_hard_line_breaks() -> None:
    source = "First line \\\\\nsecond line of text.\nAnother line \\newline\nfourth line."
    expected = "First line \\\\\nsecond line of text.\nAnother line \\newline\nfourth line."
    assert format_latex(source) == expected


def test_format_combine_preserves_heading_and_environment_boundaries() -> None:
    source = (
        "\\section{Introduction}\n"
        "This is the first sentence.\n"
        "The formula is given by:\n"
        "\\[\n"
        "  x = y\n"
        "\\]\n"
        "This concludes the section."
    )
    expected = (
        "\\section{Introduction}\n"
        "This is the first sentence.\n"
        "The formula is given by:\n"
        "\\[\n"
        "  x = y\n"
        "\\]\n"
        "This concludes the section."
    )
    assert format_latex(source) == expected


def test_format_combine_abbreviation_across_line() -> None:
    source = "As demonstrated by Smith et al.\nin their recent paper, this holds. Next sentence."
    expected = "As demonstrated by Smith et al. in their recent paper, this holds.\nNext sentence."
    assert format_latex(source) == expected


def test_format_combine_crlf_endings() -> None:
    source = "First sentence\r\nwrapped across lines. Second sentence.\r\n"
    expected = "First sentence wrapped across lines.\r\nSecond sentence.\r\n"
    assert format_latex(source) == expected
