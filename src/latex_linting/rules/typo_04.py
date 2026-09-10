from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import _SYNTAX_COMMANDS
from latex_linting.source import Finding

_PARAMETERLESS_COMMANDS = frozenset(
    {
        r"\BibTeX",
        r"\LaTeX",
        r"\TeX",
        r"\eg",
        r"\etal",
        r"\ie",
    }
)

_TERMINATING_CHARS = frozenset({".", ",", ":", ";", "!", "?", ")", "]", "}", '"', "'", "\u201d", "\u2019", "-", "~"})

_EXPLICIT_TERMINATORS = ("{}", "\\ ", "\\\t", "\\\n")


def _is_swallowed_space(source_text: str, token_end: int) -> bool:
    """Return True if whitespace following a parameterless command is swallowed without an explicit terminator."""
    after = source_text[token_end:]
    if not after or after.startswith(_EXPLICIT_TERMINATORS):
        return False
    if after[0] in _TERMINATING_CHARS:
        return False
    return after[0] in " \t\r\n"


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document for parameterless commands swallowing following whitespace."""
    syntax_depth = 0
    expecting_syntax_brace = False

    for source, token in document.traverse():
        if token.kind == "command":
            if token.value in _SYNTAX_COMMANDS:
                expecting_syntax_brace = True
            elif (
                token.math == "text"
                and syntax_depth == 0
                and token.value in _PARAMETERLESS_COMMANDS
                and _is_swallowed_space(source.text, token.end)
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
    rule_id="TYPO-04",
    explanation="Parameterless command swallows following whitespace in text mode.",
    correction="Add an explicit terminator such as '{}', '\\ ', or '~' after the command (e.g. '\\LaTeX{} ' or '\\LaTeX\\ ').",
    passing_examples=(
        r"We use \LaTeX{} for formatting.",
        r"Knuth created \TeX\ in the 1970s.",
        r"References use \BibTeX~as well.",
        r"This thesis was prepared using \LaTeX.",
    ),
    failing_examples=(
        r"We use \LaTeX is our main system.",
        r"Knuth designed \TeX was revolutionary.",
        r"Managing references with \BibTeX is standard.",
    ),
    limits=(
        r"Detects swallowed spaces after documented parameterless commands (\LaTeX, \TeX, "
        r"\BibTeX, \etal, \eg, \ie) when followed by whitespace (spaces, tabs, or newlines). "
        r"Explicit terminators ({}, \ , ~) and punctuation (., ,, :, ;, !, ?, ), ], }, quotes, "
        "dashes) pass. Excludes comments, math mode, literal environments, and syntax command arguments."
    ),
    evaluate=_evaluate,
)
