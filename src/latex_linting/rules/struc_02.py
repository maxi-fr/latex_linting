from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding

_DEEP_HEADINGS = frozenset({r"\subsubsection", r"\paragraph", r"\subparagraph"})


def _excessive_depth(document: "Document") -> Iterable[Finding]:
    """Report numbered headings nested deeper than subsection."""
    for source, token in document.traverse():
        if token.kind == "command" and token.math == "text" and token.value in _DEEP_HEADINGS:
            rest = source.text[token.end :].lstrip(" \t\r\n")
            if not rest.startswith("*"):
                yield source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="STRUC-02",
    explanation=r"Numbered headings must not exceed three levels (\chapter, \section, \subsection).",
    correction=r"Use unnumbered headings (e.g. \subsubsection* or \paragraph*) or restructure sections to stay within three numbered levels.",
    passing_examples=(
        r"\subsection{Valid Level}",
        r"\subsubsection*{Unnumbered Heading}",
        r"\paragraph*{Unnumbered Paragraph}",
    ),
    failing_examples=(
        r"\subsubsection{Too Deep}",
        r"\paragraph{Too Deep}",
        r"\subparagraph{Too Deep}",
        r"\subsubsection[Short]{Too Deep}",
    ),
    limits=(
        r"Detects literal numbered heading commands (\subsubsection, \paragraph, \subparagraph) "
        r"in text mode. Starred headings (\subsubsection*, etc.) are recognized as unnumbered "
        r"and allowed. Optional arguments (e.g. [short]) are supported. Comments and literal "
        r"environments (verbatim, lstlisting, minted) are excluded. Does not track explicit "
        r"numbering controls such as \setcounter{secnumdepth}{...} or user-defined macro expansions."
    ),
    evaluate=_excessive_depth,
)
