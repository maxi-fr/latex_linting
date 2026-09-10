from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding

_CITATION_COMMANDS = frozenset(
    {
        r"\autocite",
        r"\cite",
        r"\citeauthor",
        r"\citep",
        r"\citet",
        r"\citeyear",
        r"\footcite",
        r"\fullcite",
        r"\nocite",
        r"\parencite",
        r"\textcite",
    }
)

_ABBREVIATIONS = (
    "Dr.",
    "Prof.",
    "cf.",
    "e.g.",
    "et al.",
    "i.e.",
    "vs.",
)


def _trailing_citations(document: "Document") -> Iterable[Finding]:
    """Report citation commands placed immediately after a sentence terminal period."""
    for source, token in document.traverse():
        if token.kind != "command" or token.math != "text" or token.value not in _CITATION_COMMANDS:
            continue

        prefix = source.text[: token.start].rstrip(" \t\r\n~")
        while "\n" in prefix:
            last_line = prefix.rsplit("\n", 1)[-1].strip()
            if last_line.startswith("%"):
                prefix = prefix.rsplit("\n", 1)[0].rstrip(" \t\r\n~")
            else:
                break

        stripped_quotes = prefix.rstrip("\"'\u201d\u2019")
        if (
            stripped_quotes.endswith(".")
            and not stripped_quotes.endswith("..")
            and not stripped_quotes.endswith(_ABBREVIATIONS)
            and stripped_quotes[:-1].strip()
        ):
            yield source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="CITE-04",
    explanation="Citation placed after terminal period; citations should precede terminal punctuation.",
    correction="Move the citation command before the terminal period (e.g. '...~\\cite{...}.').",
    passing_examples=(
        r"This method was proven effective~\cite{smith2020}.",
        r"As shown in previous work~\citep[p.~5]{smith2020}.",
        r"According to~\citet{smith2020}, the bounds hold.",
    ),
    failing_examples=(
        r"This method was proven effective. \cite{smith2020}",
        r"This method was proven effective.\citep[p.~5]{smith2020}",
        r"This method was proven effective.~\autocite{smith2020}",
    ),
    limits=(
        r"Detects recognized citation commands (\cite, \citep, \citet, \autocite, \parencite, "
        r"\textcite, \footcite, \fullcite, \nocite, \citeauthor, \citeyear), including optional "
        r"arguments (e.g. [p.~5]), immediately following a sentence's terminal period in text mode. "
        "Abbreviation periods such as 'et al.' are excluded. Comments, literal code (verbatim, "
        "lstlisting, minted), and math environments are excluded. Does not evaluate whether the "
        "citation substantiates the appropriate claim."
    ),
    evaluate=_trailing_citations,
)
