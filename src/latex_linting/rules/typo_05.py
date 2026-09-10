import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_RANGE_PATTERN = re.compile(r"(?<!\w)(?<!-)(\d+(?:\.\d+)?)\s*(-)\s*(\d+(?:\.\d+)?)(?!-)(?!\w)")
_NEGATIVE_PATTERN = re.compile(r"(?<![a-zA-Z0-9_-])(-)(\d+(?:\.\d+)?)(?!-)")
_ISO_DATE_PATTERN = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document prose for single-hyphen numeric ranges and text negative numbers."""
    for source, token in iter_prose_tokens(document):
        date_spans = [m.span() for m in _ISO_DATE_PATTERN.finditer(token.value)]
        reported_offsets: set[int] = set()
        findings: list[Finding] = []

        for match in _RANGE_PATTERN.finditer(token.value):
            hyphen_start = match.start(2)
            if any(start <= hyphen_start < end for start, end in date_spans):
                continue
            offset = token.start + hyphen_start
            reported_offsets.add(offset)
            findings.append(
                source.finding(
                    offset,
                    RULE.rule_id,
                    "Numeric range uses a single hyphen instead of an en-dash '--'.",
                    "Use an en-dash '--' for numeric ranges (e.g. '10--20').",
                )
            )

        for match in _NEGATIVE_PATTERN.finditer(token.value):
            hyphen_start = match.start(1)
            offset = token.start + hyphen_start
            if offset in reported_offsets:
                continue
            reported_offsets.add(offset)
            findings.append(
                source.finding(
                    offset,
                    RULE.rule_id,
                    "Negative number uses a text hyphen instead of math mode minus or en-dash.",
                    "Use math mode (e.g. '$-5$') or an en-dash for negative numbers.",
                )
            )

        findings.sort(key=lambda f: (f.line, f.column))
        yield from findings


RULE = Rule(
    rule_id="TYPO-05",
    explanation="Incorrect hyphen used for numeric range or text negative number.",
    correction="Use an en-dash '--' for numeric ranges (e.g. '10--20') and math mode for negative numbers (e.g. '$-5$').",
    passing_examples=(
        r"We tested values from 10--20 units.",
        r"Results are shown on pp.~5--10 and pages~12--15.",
        r"The temperature dropped to $-5$ degrees Celsius.",
        r"We develop a state-of-the-art closed-loop controller.",
    ),
    failing_examples=(
        r"We tested values from 10-20 units.",
        r"Results are shown on pp. 5-10 and pages 12-15.",
        r"The temperature dropped to -5 degrees Celsius.",
        r"Offsets of -10 and -20 were observed.",
    ),
    limits=(
        r"Detects single hyphens in numeric ranges (e.g. '10-20', 'pp. 5-10') and text negative "
        r"numbers (e.g. '-5') in text mode. En-dashes ('--'), em-dashes ('---'), math mode minus "
        r"('$-5$', '$x - y$'), and compound words ('state-of-the-art', 'closed-loop', 'COVID-19', "
        r"'10-fold') pass. Comments, literal code (\verb, verbatim, lstlisting), and syntax "
        "command arguments are excluded."
    ),
    evaluate=_evaluate,
)
