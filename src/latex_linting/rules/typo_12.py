import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_context import iter_prose_tokens
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_ACRO_USAGE_COMMANDS = frozenset(
    {
        r"\ac",
        r"\Ac",
        r"\acs",
        r"\Acs",
        r"\acl",
        r"\Acl",
        r"\acf",
        r"\Acf",
        r"\acp",
        r"\Acp",
        r"\acsp",
        r"\Acsp",
        r"\aclp",
        r"\Aclp",
        r"\acfp",
        r"\Acfp",
        r"\iac",
        r"\Iac",
        r"\acuse",
        r"\acreset",
    }
)

_ROMAN_NUMERALS = frozenset(
    {
        "II",
        "III",
        "IV",
        "VI",
        "VII",
        "VIII",
        "IX",
        "XI",
        "XII",
        "XIII",
        "XIV",
        "XV",
        "XVI",
        "XVII",
        "XVIII",
        "XIX",
        "XX",
        "XXI",
        "XXII",
        "XXIII",
        "XXIV",
        "XXV",
        "XXX",
        "XL",
        "L",
    }
)

_UNIVERSAL_TERMS = frozenset(
    {
        "ASCII",
        "BibTeX",
        "DIN",
        "DNA",
        "EPS",
        "EU",
        "HTML",
        "HTTP",
        "HTTPS",
        "IEEE",
        "ISO",
        "JPEG",
        "JPG",
        "JSON",
        "LaTeX",
        "NIST",
        "PDF",
        "PNG",
        "RNA",
        "SI",
        "SVG",
        "TeX",
        "UK",
        "URI",
        "URL",
        "US",
        "USA",
        "USB",
        "UTF",
        "XML",
    }
)

_MANUAL_INTRO_PATTERN = re.compile(r"\(([A-Z]{2,6}s?|[A-Z][a-z][A-Z0-9]{1,4})\)")


@dataclass(frozen=True)
class _AcronymDecl:
    """Store declared acronym identifier and short/long forms."""

    acronym_id: str
    short: str
    long: str | None
    source: Source
    start: int


def _skip_ignorable(tokens: Sequence[Token], idx: int) -> int:
    """Advance index over whitespace and comment tokens."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _extract_braced_arg(tokens: Sequence[Token], start_idx: int) -> tuple[str, int]:
    """Extract argument within curly braces, returning contents and next token index."""
    idx = _skip_ignorable(tokens, start_idx)
    if idx >= len(tokens) or tokens[idx].kind != "brace" or tokens[idx].value != "{":
        return "", idx
    brace_depth = 1
    idx += 1
    parts: list[str] = []
    while idx < len(tokens) and brace_depth > 0:
        cur = tokens[idx]
        if cur.kind == "brace":
            brace_depth += 1 if cur.value == "{" else -1
        if brace_depth > 0 and cur.kind != "comment":
            parts.append(cur.value)
        idx += 1
    return "".join(parts).strip(), idx


def _extract_property(properties: str, key: str) -> str | None:
    """Extract a key-value property from a DeclareAcronym property string."""
    pattern = re.compile(rf"\b{re.escape(key)}\s*=\s*(?:\{{([^}}]+)\}}|([^,}}\r\n]+))")
    match = pattern.search(properties)
    if match is None:
        return None
    val = match.group(1) if match.group(1) is not None else match.group(2)
    return val.strip() if val else None


def _collect_declared_acronyms(document: "Document") -> dict[str, _AcronymDecl]:
    """Collect all acronym declarations across the document sources."""
    declarations: dict[str, _AcronymDecl] = {}
    for source in document.sources:
        tokens = scan(source.text)
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.kind == "command" and token.value == r"\DeclareAcronym":
                acronym_id, idx = _extract_braced_arg(tokens, idx + 1)
                properties, idx = _extract_braced_arg(tokens, idx)
                if acronym_id:
                    short = _extract_property(properties, "short")
                    long = _extract_property(properties, "long")
                    if short:
                        declarations[acronym_id] = _AcronymDecl(
                            acronym_id=acronym_id,
                            short=short,
                            long=long,
                            source=source,
                            start=token.start,
                        )
                continue
            idx += 1
    return declarations


def _skip_optional_bracket(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past an optional bracket argument if present."""
    idx = _skip_ignorable(tokens, idx)
    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.startswith("["):
        bracket_depth = 0
        while idx < len(tokens):
            val = tokens[idx].value
            bracket_depth += val.count("[") - val.count("]")
            idx += 1
            if bracket_depth <= 0:
                break
    return idx


def _check_undefined_references(
    document: "Document",
    declared: dict[str, _AcronymDecl],
) -> list[Finding]:
    """Report acro usage commands that reference undeclared acronym keys."""
    findings: list[Finding] = []
    for source in document.sources:
        tokens = scan(source.text)
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.kind == "command" and token.value in _ACRO_USAGE_COMMANDS:
                next_idx = idx + 1
                if (
                    next_idx < len(tokens)
                    and tokens[next_idx].kind == "text"
                    and tokens[next_idx].value.startswith("*")
                ):
                    next_idx += 1
                next_idx = _skip_optional_bracket(tokens, next_idx)
                acronym_id, next_idx = _extract_braced_arg(tokens, next_idx)
                if acronym_id and acronym_id not in declared:
                    findings.append(
                        source.finding(
                            token.start,
                            RULE.rule_id,
                            f"Acronym '{acronym_id}' is referenced via '{token.value}' but not declared with \\DeclareAcronym.",
                            f"Declare the acronym using \\DeclareAcronym{{{acronym_id}}}{{short = ..., long = ...}}.",
                        )
                    )
                idx = next_idx
                continue
            idx += 1
    return findings


_MIN_PLURAL_ACRONYM_LEN = 2


def _is_exempt_token(token_text: str) -> bool:
    """Return True if token is an allowed Roman numeral or universal term."""
    base = (
        token_text[:-1]
        if token_text.endswith("s") and len(token_text) > _MIN_PLURAL_ACRONYM_LEN and token_text[:-1].isupper()
        else token_text
    )
    return base in _ROMAN_NUMERALS or base in _UNIVERSAL_TERMS or token_text in _UNIVERSAL_TERMS


def _check_prose_acronyms(
    document: "Document",
    declared: dict[str, _AcronymDecl],
) -> list[Finding]:
    """Scan document prose for manual acronym introductions and bare declared acronyms."""
    findings: list[Finding] = []
    short_to_decl = {decl.short: decl for decl in declared.values()}

    seen_shorts: set[str] = set()
    decl_patterns: list[tuple[_AcronymDecl, re.Pattern[str]]] = []
    for decl in declared.values():
        if decl.short and decl.short not in seen_shorts and all(c.isalnum() or c in "-_" for c in decl.short):
            seen_shorts.add(decl.short)
            decl_patterns.append((decl, re.compile(rf"\b{re.escape(decl.short)}(?:s)?\b")))

    for source, token in iter_prose_tokens(document):
        manual_spans: list[tuple[int, int]] = []

        for match in _MANUAL_INTRO_PATTERN.finditer(token.value):
            acro_text = match.group(1)
            if _is_exempt_token(acro_text):
                continue

            offset = token.start + match.start()
            manual_spans.append((match.start(), match.end()))

            if acro_text in short_to_decl:
                decl = short_to_decl[acro_text]
                findings.append(
                    source.finding(
                        offset,
                        RULE.rule_id,
                        f"Acronym '{acro_text}' is declared in acro; use \\ac{{{decl.acronym_id}}} instead of manual parentheses.",
                        f"Replace with \\ac{{{decl.acronym_id}}}.",
                    )
                )
            else:
                findings.append(
                    source.finding(
                        offset,
                        RULE.rule_id,
                        f"Do not manually introduce acronym '{acro_text}' in parentheses; manage abbreviations using the acro package.",
                        f"Declare with \\DeclareAcronym{{{acro_text.lower()}}}{{short = {acro_text}, long = {{...}}}} and use \\ac{{{acro_text.lower()}}}.",
                    )
                )

        for decl, pattern in decl_patterns:
            for match in pattern.finditer(token.value):
                start, end = match.span()
                if any(m_start <= start and end <= m_end for m_start, m_end in manual_spans):
                    continue

                offset = token.start + match.start()
                findings.append(
                    source.finding(
                        offset,
                        RULE.rule_id,
                        f"Acronym '{decl.short}' is declared in acro; use \\ac{{{decl.acronym_id}}} instead of bare text.",
                        f"Replace '{match.group()}' with \\ac{{{decl.acronym_id}}}.",
                    )
                )

    return findings


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Enforce acro package abbreviation management across document declarations and prose."""
    declared = _collect_declared_acronyms(document)
    findings: list[Finding] = []
    findings.extend(_check_undefined_references(document, declared))
    findings.extend(_check_prose_acronyms(document, declared))
    return findings


RULE = Rule(
    rule_id="TYPO-12",
    explanation="Manage abbreviations using the acro package: declare acronyms with \\DeclareAcronym and reference them with \\ac.",
    correction="Declare the abbreviation with \\DeclareAcronym and reference it using \\ac{<id>}.",
    passing_examples=(
        "\\DeclareAcronym{mpc}{short = MPC, long = Model Predictive Control}\nWe apply \\ac{mpc} to the system.",
        "The conditions (II) and (IV) hold under portable document format (PDF).",
    ),
    failing_examples=(
        "We introduce Model Predictive Control (MPC) for trajectory tracking.",
        "\\DeclareAcronym{svm}{short = SVM, long = Support Vector Machine}\nWe test bare SVM classifiers.",
        "We evaluate \\ac{unknown_acronym} on the benchmark.",
    ),
    limits=(
        "Detects manual acronym introductions in parentheses such as (MPC) or (SoC), bare occurrences of "
        "declared acronym short forms, and acro usage commands referencing undeclared keys. Excludes Roman "
        "numerals (e.g. (II), (IV)), universal format and standard terms (e.g. (PDF), (URL), (IEEE)), "
        "math mode, comments, verbatim/code environments, and syntax command arguments."
    ),
    evaluate=_evaluate,
)
