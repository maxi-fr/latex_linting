import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.source import Finding

_CATEGORY_NOUN_PATTERN = re.compile(
    r"\b(Figures?|Fig\.|Tables?|Tab\.|Sections?|Sec\.|Chapters?|Ch\.|Equations?|Eq\.|Pages?|pp?\.)[ \t\r\n]+(\d+(?:\.\d+)*)\b"
)

_TITLE_PATTERN = re.compile(r"\b(Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.)[ \t\r\n]+([A-Z\xc0-\xd6\xd8-\xdf][a-zA-Z\xc0-\xff]*)")

_TIME_PATTERN = re.compile(r"\b(\d+(?:[:.]\d+)?)[ \t\r\n]+(?:(p\.m\.|a\.m\.)(?![a-zA-Z0-9])|Uhr\b)")

_RECOGNIZED_UNITS = (
    "kg",
    "g",
    "mg",
    "ug",
    "ng",
    "km",
    "cm",
    "mm",
    "um",
    "nm",
    "pm",
    "ms",
    "ns",
    "ps",
    "s",
    "Hz",
    "kHz",
    "MHz",
    "GHz",
    "THz",
    "kV",
    "mV",
    "MV",
    "V",
    "kA",
    "mA",
    "uA",
    "A",
    "kW",
    "MW",
    "GW",
    "mW",
    "W",
    "kJ",
    "MJ",
    "GJ",
    "mJ",
    "J",
    "kN",
    "MN",
    "mN",
    "N",
    "kPa",
    "MPa",
    "GPa",
    "hPa",
    "Pa",
    "bar",
    "mbar",
    "dB",
    "dBm",
    "dBi",
    "rad",
    "mrad",
    "deg",
    "mol",
    "mmol",
    "Ohm",
    "K",
    "F",
    "H",
    "T",
    "C",
    "m",
)

_UNIT_REGEX = "|".join(sorted(_RECOGNIZED_UNITS, key=len, reverse=True))

_NUMBER_UNIT_PATTERN = re.compile(rf"\b(\d+(?:[.,]\d+)?)[ \t\r\n]+({_UNIT_REGEX})\b")


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Scan document prose for fixed expressions and number-unit pairs lacking nonbreaking space."""
    for source, token in iter_prose_tokens(document):
        matches: list[tuple[int, int]] = []
        for pattern in (_CATEGORY_NOUN_PATTERN, _TITLE_PATTERN, _TIME_PATTERN, _NUMBER_UNIT_PATTERN):
            matches.extend((m.start(), m.end()) for m in pattern.finditer(token.value))

        matches.sort(key=lambda m: m[0])
        for start, _ in matches:
            offset = token.start + start
            yield source.finding(offset, RULE.rule_id, RULE.explanation, RULE.correction)


RULE = Rule(
    rule_id="TYPO-02",
    explanation="Fixed expression or number-unit form separated by regular space instead of nonbreaking space '~'.",
    correction="Use a nonbreaking space '~' (or thin space '\\,' / siunitx command for units) instead of regular whitespace.",
    passing_examples=(
        r"As seen in Figure~1, Table~2, Section~3, and Chapter~4.",
        r"Dr.~Müller and Prof.~Smith gave the lecture.",
        r"The meeting is at 3~p.m. or 3~Uhr.",
        r"The distance is 10~m or 10\,m or \SI{10}{m}.",
    ),
    failing_examples=(
        r"As seen in Figure 1 and Table 2.",
        r"Dr. Müller and Prof. Smith gave the lecture.",
        r"The meeting is at 3 p.m. or 3 Uhr.",
        r"The distance is 10 m and the mass is 5 kg.",
    ),
    limits=(
        r"Checks nonbreaking spaces (~) in fixed expressions: category nouns with numbers "
        r"(Figure, Fig., Table, Tab., Section, Sec., Chapter, Ch., Equation, Eq., Page, p., pp.), "
        r"titles with names (Dr., Prof., Mr., Mrs., Ms.), and times (p.m., a.m., Uhr). "
        r"Checks recognizable number-unit forms in text mode with units (m, km, cm, mm, um, nm, s, "
        r"ms, ns, kg, g, mg, V, mV, kV, A, mA, W, kW, MW, Hz, kHz, MHz, GHz, Pa, bar, dB, etc.). "
        r"Accepts nonbreaking space (~), thin space (\,), and unit commands (\SI, \qty, \unit). "
        r"Excludes math mode, comments, literal code, and syntax command arguments (such as \label, \ref, \cite)."
    ),
    evaluate=_evaluate,
)
