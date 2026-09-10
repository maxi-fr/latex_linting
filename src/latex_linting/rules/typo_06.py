import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_DOUBLE_QUOTE_PATTERN = re.compile(r'"')
_OPENING_SINGLE_QUOTE_PATTERN = re.compile(r"(?:^|[\s(\[{<:;~])('{1,2})(?=[a-zA-Z0-9])")


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document prose for straight double and single quotation marks."""
    for source, token in iter_prose_tokens(document):
        findings: list[Finding] = []

        for match in _DOUBLE_QUOTE_PATTERN.finditer(token.value):
            offset = token.start + match.start()
            findings.append(
                source.finding(
                    offset,
                    RULE.rule_id,
                    "Straight double quote '\"' used in text mode.",
                    "Use LaTeX quotation marks (``word'' or \\enquote{word}).",
                )
            )

        for match in _OPENING_SINGLE_QUOTE_PATTERN.finditer(token.value):
            offset = token.start + match.start(1)
            findings.append(
                source.finding(
                    offset,
                    RULE.rule_id,
                    "Straight single quote used as quotation mark in text mode.",
                    "Use LaTeX quotation marks (``word'' or \\enquote{word}) or backtick (`word').",
                )
            )

        findings.sort(key=lambda f: (f.line, f.column))
        yield from findings


RULE = Rule(
    rule_id="TYPO-06",
    explanation="Straight quotation mark used in text mode.",
    correction="Use LaTeX quotation marks (``word'' or \\enquote{word}) or a backtick (`word').",
    passing_examples=(
        r"We write ``double-quoted'' prose.",
        r"We write `single-quoted' prose.",
        r"We use \enquote{enquoted} text.",
        r"Don't assume it's the author's work with students' data.",
    ),
    failing_examples=(
        r'This is "quoted" text.',
        r"This is 'single-quoted' text.",
        r'We note that "results" vary.',
        r"He stated: 'Results are preliminary.'",
    ),
    limits=(
        r"Detects straight double quotes (\") and straight single quotes (') used as quotation marks "
        r"in text mode. Apostrophes in contractions (don't) and possessives (author's, students') "
        r"pass, as do LaTeX quotation marks (``...'' and `...'), \enquote{...}, literal code "
        r"(\verb, verbatim, lstlisting, minted), escaped accent commands (\"a, \'e, \`e), and "
        r"math mode ($f'(x)$)."
    ),
    evaluate=_evaluate,
)
