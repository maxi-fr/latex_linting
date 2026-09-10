import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.math_context import ContextTracker
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_BARE_RECOGNIZED_UNITS = frozenset(
    {
        "kg",
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
        "us",
        "ns",
        "ps",
        "Hz",
        "kHz",
        "MHz",
        "GHz",
        "THz",
        "mHz",
        "mV",
        "kV",
        "MV",
        "uV",
        "mA",
        "kA",
        "uA",
        "kW",
        "MW",
        "GW",
        "mW",
        "kJ",
        "MJ",
        "GJ",
        "mJ",
        "kN",
        "MN",
        "mN",
        "Pa",
        "kPa",
        "MPa",
        "GPa",
        "hPa",
        "bar",
        "mbar",
        "rad",
        "mrad",
        "deg",
        "dB",
        "dBm",
        "dBi",
        "mol",
        "mmol",
        "kmol",
    }
)

_SINGLE_LETTER_UNITS = frozenset(
    {"m", "s", "g", "V", "A", "W", "J", "N", "K", "F", "H", "T", "C", "Bq", "Gy", "Sv", "lx", "lm"}
)

_ALL_RECOGNIZED_UNITS = _BARE_RECOGNIZED_UNITS | _SINGLE_LETTER_UNITS | {"Ohm", r"\Omega"}

_BARE_UNIT_PATTERN = re.compile(r"(?<![a-zA-Z\\])\b(\d+(?:\.\d+)?|\d+(?:,\d+)?)\s*~?\s*([a-zA-Z]+)\b")

_NUMBER_AT_END = re.compile(r"(?<![a-zA-Z\\])\b(\d+(?:\.\d+)?|\d+(?:,\d+)?)(?:\^[0-9]+|\^\{[0-9+-]+\})?\s*~?\s*$")

_UNIT_FORMAT_COMMANDS = frozenset({r"\mathrm", r"\text", r"\operatorname"})


def _is_recognized_unit(unit_str: str) -> bool:
    """Return True if unit_str is a recognizable physical unit."""
    cleaned = unit_str.strip()
    if not cleaned:
        return False
    if cleaned in _ALL_RECOGNIZED_UNITS:
        return True
    parts = re.split(r"[/.*^+\-\s\\]+", cleaned)
    clean_parts = [p for p in parts if p and not p.isdigit()]
    return bool(clean_parts) and all(p in _ALL_RECOGNIZED_UNITS for p in clean_parts)


def _peek_unit_argument(tokens: tuple[Token, ...], cmd_idx: int) -> str | None:
    """Extract inner text from a unit command's brace argument, or None if malformed."""
    idx = cmd_idx + 1
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1

    if idx >= len(tokens) or tokens[idx].value != "{":
        return None

    idx += 1
    parts: list[str] = []
    depth = 1
    while idx < len(tokens) and depth > 0:
        cur = tokens[idx]
        if cur.kind == "brace":
            if cur.value == "{":
                depth += 1
            elif cur.value == "}":
                depth -= 1
        elif cur.kind != "comment":
            parts.append(cur.value)
        idx += 1

    return "".join(parts).strip() if depth == 0 else None


def _check_bare_units(source: Source, token: Token) -> Iterable[Finding]:
    """Report numbers directly adjacent to recognized bare units."""
    for match in _BARE_UNIT_PATTERN.finditer(token.value):
        unit = match.group(2)
        if unit in _BARE_RECOGNIZED_UNITS:
            num_offset = token.start + match.start(1)
            yield source.finding(num_offset, RULE.rule_id, RULE.explanation, RULE.correction)


def _check_unit_command_lookahead(source: Source, token: Token, tokens: tuple[Token, ...], idx: int) -> Finding | None:
    """Report numbers followed by a unit command without thin spacing."""
    match_end = _NUMBER_AT_END.search(token.value)
    if not match_end:
        return None

    look = idx + 1
    while look < len(tokens) and (
        tokens[look].kind == "comment" or (tokens[look].kind == "text" and tokens[look].value.isspace())
    ):
        look += 1

    if look < len(tokens):
        next_tok = tokens[look]
        if next_tok.kind == "command" and next_tok.value in _UNIT_FORMAT_COMMANDS:
            unit_content = _peek_unit_argument(tokens, look)
            if unit_content is not None and _is_recognized_unit(unit_content):
                num_offset = token.start + match_end.start(1)
                return source.finding(num_offset, RULE.rule_id, RULE.explanation, RULE.correction)
    return None


def _check_source_math_06(source: Source) -> Iterable[Finding]:
    """Scan tokens in a single source for number-unit spacing violations."""
    tokens = scan(source.text)
    tracker = ContextTracker()

    for idx, token in enumerate(tokens):
        in_math = token.math in ("inline", "display")
        if not in_math:
            tracker.reset_all()
            continue

        tracker.handle_token(token)
        ctx = tracker.current_context(in_math=in_math)
        if ctx.in_non_math or ctx.in_unit_command:
            continue

        if token.kind == "text":
            yield from _check_bare_units(source, token)
            cmd_finding = _check_unit_command_lookahead(source, token, tokens, idx)
            if cmd_finding is not None:
                yield cmd_finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report number-unit spacing violations across the document."""
    for source in document.sources:
        yield from _check_source_math_06(source)


RULE = Rule(
    rule_id="MATH-06",
    explanation=(
        r"In math mode, numbers and units must be separated by a thin space (\,) "
        "or formatted using siunitx commands."
    ),
    correction=(
        r"Insert a thin space (\,) between the number and unit (e.g. 10\,\mathrm{kg} "
        r"or 10\,\text{m}) or use siunitx commands like \SI, \qty, or \unit."
    ),
    passing_examples=(
        r"$10\,\mathrm{kg}$",
        r"$10\,\text{m}$",
        r"$10\,kg$",
        r"\SI{10}{kg}",
        r"\qty{10}{\meter}",
        r"$2x + 3a$",
        r"$10m$",
        r"\[ F = 100\,\mathrm{N} \,.\]",
    ),
    failing_examples=(
        r"$10\mathrm{kg}$",
        r"$10 \mathrm{kg}$",
        r"$10\text{m}$",
        r"$10 \text{m}$",
        "$10kg$",
        "$10 kg$",
        r"\[ v = 50km \]",
    ),
    limits=(
        r"Detects numbers followed directly or with regular whitespace by recognizable units "
        r"(\mathrm{...}, \text{...}, or bare units like kg, Hz, kHz, MHz, GHz, mm, cm, km, "
        "mV, mA, kW, MW, ms, rad, deg, dB) in inline and display math. Accepts thin space "
        r"(\,) and siunitx commands (\SI, \qty, \unit). Does not infer ambiguous variable "
        "products (e.g. 2x, 3a, 4y) or bare single-letter symbols (e.g. 10m, 5s) without "
        r"\mathrm or \text. Comments, literal code, and nested non-math commands are excluded."
    ),
    evaluate=_evaluate,
)
