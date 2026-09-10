from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding

_REFERENCE_COMMANDS = frozenset(
    {
        r"\autoref",
        r"\Cref",
        r"\cref",
        r"\eqref",
        r"\pageref",
        r"\ref",
    }
)

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

_TYPO_01_COMMANDS = _REFERENCE_COMMANDS | _CITATION_COMMANDS

_NON_PROSE_SYNTAX_COMMANDS = frozenset(
    {
        r"\addbibresource",
        r"\addtocounter",
        r"\bibliography",
        r"\bibliographystyle",
        r"\documentclass",
        r"\include",
        r"\includegraphics",
        r"\includeonly",
        r"\input",
        r"\label",
        r"\nocite",
        r"\pagenumbering",
        r"\pagestyle",
        r"\RequirePackage",
        r"\setcounter",
        r"\setlength",
        r"\subfile",
        r"\thispagestyle",
        r"\url",
        r"\usepackage",
    }
)

_ABBREVIATIONS = (
    "et al.",
    "e.g.",
    "i.e.",
    "etc.",
    "Dr.",
    "Prof.",
    "Mr.",
    "Mrs.",
    "Ms.",
    "vs.",
    "cf.",
    "Fig.",
    "Figs.",
    "Tab.",
    "Tabs.",
    "Sec.",
    "Secs.",
    "Ch.",
    "Chs.",
    "Eq.",
    "Eqs.",
    "p.",
    "pp.",
    "vol.",
    "no.",
    "al.",
)

_OPENING_DELIMITERS = frozenset({"(", "[", "{", '"', "'", "``", "\u201c", "\u2018"})


def _is_sentence_boundary(text: str) -> bool:
    """Return True if text ends with terminal sentence punctuation that is not an abbreviation."""
    stripped_quotes = text.rstrip("\"'\u201d\u2019")
    return (
        stripped_quotes.endswith((".", "!", "?"))
        and not stripped_quotes.endswith("..")
        and not stripped_quotes.endswith(_ABBREVIATIONS)
    )


def _inspect_line_start(prefix: str, line_start: int) -> bool:
    """Check whether a command beginning a line violates nonbreaking space conventions."""
    lines_above = prefix[: line_start - 1].split("\n")
    saw_blank_line = False
    prev_content = ""
    for line in reversed(lines_above):
        stripped_line = line.strip()
        if not stripped_line:
            saw_blank_line = True
            continue
        if stripped_line.startswith("%"):
            continue
        comment_idx = line.find("%")
        prev_content = line[:comment_idx].rstrip() if comment_idx != -1 else line.rstrip()
        break

    if saw_blank_line or not prev_content or prev_content.endswith("~"):
        return False

    return not _is_sentence_boundary(prev_content)


def _inspect_same_line(line_before: str) -> bool:
    """Check whether a command following text on the same line violates nonbreaking space conventions."""
    if line_before.endswith("~") or line_before.rstrip(" \t").endswith("~"):
        return False
    if line_before[-1] not in " \t":
        return False
    stripped = line_before.rstrip(" \t")
    if stripped.endswith(tuple(_OPENING_DELIMITERS)):
        return False
    return not _is_sentence_boundary(stripped)


def _inspect_preceding(text: str, pos: int) -> bool:
    """Return True if the command at pos is preceded by regular space/newline instead of nonbreaking space."""
    prefix = text[:pos]
    if not prefix:
        return False

    line_start = prefix.rfind("\n") + 1
    line_before = prefix[line_start:pos]
    if not line_before.strip():
        return _inspect_line_start(prefix, line_start)
    return _inspect_same_line(line_before)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document for reference and citation commands preceded by regular whitespace."""
    syntax_depth = 0
    expecting_syntax_brace = False

    for source, token in document.traverse():
        if token.kind == "command":
            if token.value in _NON_PROSE_SYNTAX_COMMANDS:
                expecting_syntax_brace = True
            elif (
                token.math == "text"
                and syntax_depth == 0
                and token.value in _TYPO_01_COMMANDS
                and _inspect_preceding(source.text, token.start)
            ):
                yield source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction)
            continue

        if token.kind == "brace":
            if token.value == "{":
                if expecting_syntax_brace:
                    syntax_depth += 1
                    expecting_syntax_brace = False
                elif syntax_depth > 0:
                    syntax_depth += 1
            elif token.value == "}" and syntax_depth > 0:
                syntax_depth -= 1


RULE = Rule(
    rule_id="TYPO-01",
    explanation="Reference or citation command preceded by regular space or newline instead of nonbreaking space '~'.",
    correction="Use a nonbreaking space '~' before the command (e.g. 'Figure~\\ref{...}' or 'Smith~\\cite{...}').",
    passing_examples=(
        r"As shown in Figure~\ref{fig:arch}, the system operates.",
        r"According to Smith~\cite{smith2020}, this holds.",
        r"See Section~\ref{sec:intro} for details.",
    ),
    failing_examples=(
        r"As shown in Figure \ref{fig:arch}, the system operates.",
        r"According to Smith \cite{smith2020}, this holds.",
        r"See Section \ref{sec:intro} for details.",
    ),
    limits=(
        r"Checks nonbreaking spaces (~) before supported reference commands (\ref, \eqref, "
        r"\autoref, \cref, \Cref, \pageref) and citation commands (\cite, \citep, \citet, "
        r"\autocite, \parencite, \textcite, \footcite, \fullcite, \nocite, \citeauthor, \citeyear) "
        "where prose calls for a preceding space. Commands at prose boundaries (beginning of line, "
        "sentence start, after opening parenthesis, bracket, or brace) or already preceded by ~ pass. "
        "Handles optional arguments and multiline input. Comments, math mode, literal environments, "
        "and syntax command arguments are excluded."
    ),
    evaluate=_evaluate,
)
