import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_CATEGORY_WORDS: dict[str, frozenset[str]] = {
    "fig": frozenset(
        {
            "figure",
            "figures",
            "fig.",
            "figs.",
            "fig",
            "abbildung",
            "abbildungen",
            "abb.",
            "abb",
        }
    ),
    "tab": frozenset(
        {
            "table",
            "tables",
            "tab.",
            "tabs.",
            "tab",
            "tabelle",
            "tabellen",
        }
    ),
    "sec": frozenset(
        {
            "section",
            "sections",
            "sec.",
            "secs.",
            "sec",
            "subsection",
            "subsections",
            "subsec.",
            "subsecs.",
            "subsubsection",
            "subsubsections",
            "abschnitt",
            "abschnitte",
            "abschnitts",
            "abschnitten",
            "abschn.",
            "abschn",
            "unterabschnitt",
            "unterabschnitte",
        }
    ),
    "ch": frozenset(
        {
            "chapter",
            "chapters",
            "chap.",
            "chaps.",
            "chap",
            "ch.",
            "chs.",
            "ch",
            "kapitel",
            "kapitels",
            "kap.",
            "kap",
        }
    ),
    "cha": frozenset(
        {
            "chapter",
            "chapters",
            "chap.",
            "chaps.",
            "chap",
            "ch.",
            "chs.",
            "ch",
            "kapitel",
            "kapitels",
            "kap.",
            "kap",
        }
    ),
    "app": frozenset(
        {
            "appendix",
            "appendices",
            "app.",
            "apps.",
            "app",
            "anhang",
            "anhangs",
            "anhänge",
            "anhängen",
            "anh.",
            "anh",
        }
    ),
    "lst": frozenset(
        {
            "listing",
            "listings",
            "lst.",
            "lsts.",
            "lst",
            "code",
            "quellcode",
            "programm",
        }
    ),
    "listing": frozenset(
        {
            "listing",
            "listings",
            "lst.",
            "lsts.",
            "lst",
            "code",
            "quellcode",
            "programm",
        }
    ),
}

_PAGE_WORDS = frozenset(
    {
        "page",
        "pages",
        "p.",
        "pp.",
        "p",
        "pp",
        "seite",
        "seiten",
        "s.",
        "s",
    }
)

_ALL_CATEGORY_WORDS = frozenset().union(
    *_CATEGORY_WORDS.values(),
    _PAGE_WORDS,
    {
        "algorithm",
        "algorithms",
        "alg.",
        "algs.",
        "algorithmus",
        "algorithmen",
        "theorem",
        "theorems",
        "thm.",
        "thms.",
        "theoreme",
        "satz",
        "sätze",
        "lemma",
        "lemmas",
        "lemmata",
        "corollary",
        "corollaries",
        "korollar",
        "korollare",
        "definition",
        "definitions",
        "def.",
        "defs.",
        "definitionen",
        "example",
        "examples",
        "ex.",
        "exs.",
        "beispiel",
        "beispiele",
        "bsp.",
        "part",
        "parts",
        "teil",
        "teile",
        "step",
        "steps",
        "schritt",
        "schritte",
        "case",
        "cases",
        "fall",
        "fälle",
        "rule",
        "rules",
        "regel",
        "regeln",
        "line",
        "lines",
        "zeile",
        "zeilen",
    },
)

_COORDINATORS = frozenset({"and", "und", "or", "oder", "to", "bis", "sowie", "--", "-", ","})
_OPENING_DELIMITERS = "([{\"'`\u201c\u2018"
_CLOSING_DELIMITERS = ")]}\"'`\u201d\u2019"
_SUBFIGURE_SUFFIX = re.compile(r"^(?:\([a-zA-Z0-9]+\)|[a-zA-Z](?=[\s~,]))\s*")


def _skip_ignorable(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past whitespace and comments."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _extract_braced_argument(tokens: Sequence[Token], cmd_idx: int) -> tuple[str, int]:
    """Extract braced argument text following a command, skipping comments and whitespace."""
    idx = _skip_ignorable(tokens, cmd_idx + 1)
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


def _clean_preceding_text(raw_text: str) -> str:
    """Strip trailing whitespace, nonbreaking spaces, and comments from preceding text."""
    clean = raw_text.rstrip(" \t\r\n~")
    while "\n" in clean:
        last_line = clean.rsplit("\n", 1)[-1].strip()
        if last_line.startswith("%"):
            clean = clean.rsplit("\n", 1)[0].rstrip(" \t\r\n~")
        else:
            break
    return clean


def _extract_last_word(clean_text: str) -> str:
    """Extract the last word from cleaned preceding text, stripping delimiters."""
    if not clean_text:
        return ""
    words = clean_text.split()
    if not words:
        return ""
    last_token = words[-1]
    return last_token.lstrip(_OPENING_DELIMITERS).rstrip(_CLOSING_DELIMITERS)


_PREFIX_TO_CATEGORY = (
    ("fig:", "fig"),
    ("tab:", "tab"),
    ("sec:", "sec"),
    ("ch:", "ch"),
    ("cha:", "ch"),
    ("app:", "app"),
    ("lst:", "lst"),
    ("listing:", "lst"),
)


def _determine_expected_category(target: str) -> str:
    """Map a label target prefix to its expected category key."""
    for prefix, cat in _PREFIX_TO_CATEGORY:
        if target.startswith(prefix):
            return cat
    return "any"


def _is_coordinated(
    intervening: str,
    last_ref_category: str | None,
    expected_category: str,
) -> bool:
    """Check whether intervening text between references represents a coordinated series."""
    if last_ref_category is None:
        return False
    if last_ref_category != expected_category and "any" not in (expected_category, last_ref_category):
        return False
    if re.search(r"\n\s*\n", intervening):
        return False

    remainder = _SUBFIGURE_SUFFIX.sub("", intervening.strip())
    tokens = [t.strip(" \t~,") for t in remainder.split() if t.strip(" \t~,")]
    if not tokens and "," in remainder:
        return True
    return bool(tokens) and all(t in _COORDINATORS for t in tokens)


def _match_category(word: str, expected_category: str) -> str | None:
    """Return None if valid, or an error status if category does not match."""
    w_lower = word.lower()
    w_no_dot = w_lower.rstrip(".")

    if expected_category == "page":
        return None if (w_lower in _PAGE_WORDS or w_no_dot in _PAGE_WORDS) else "page"

    if expected_category == "any":
        return None if (w_lower in _ALL_CATEGORY_WORDS or w_no_dot in _ALL_CATEGORY_WORDS) else "any"

    allowed = _CATEGORY_WORDS.get(expected_category, frozenset())
    if w_lower in allowed or w_no_dot in allowed:
        return None

    return "mismatch" if (w_lower in _ALL_CATEGORY_WORDS or w_no_dot in _ALL_CATEGORY_WORDS) else "missing"


def _suggest_example(expected_category: str, target: str) -> str:
    """Produce an appropriate example category prefix for corrections."""
    suggestions = {
        "fig": f"Figure~\\ref{{{target}}}",
        "tab": f"Table~\\ref{{{target}}}",
        "sec": f"Section~\\ref{{{target}}}",
        "ch": f"Chapter~\\ref{{{target}}}",
        "app": f"Appendix~\\ref{{{target}}}",
        "lst": f"Listing~\\ref{{{target}}}",
        "page": f"page~\\pageref{{{target}}}",
    }
    return suggestions.get(expected_category, f"Section~\\ref{{{target}}}")


def _check_source(source: Source) -> Iterable[Finding]:
    """Scan a source file for reference commands lacking required category nouns."""
    tokens = scan(source.text)
    last_ref: tuple[str, int] | None = None

    for idx, token in enumerate(tokens):
        if token.kind != "command" or token.math != "text" or token.value not in (r"\ref", r"\pageref"):
            continue

        target, end_idx = _extract_braced_argument(tokens, idx)
        if not target or target.startswith("eq:"):
            continue

        ref_end_offset = tokens[end_idx - 1].end if end_idx > idx else token.end
        expected_cat = "page" if token.value == r"\pageref" else _determine_expected_category(target)

        if last_ref is not None:
            intervening = source.text[last_ref[1] : token.start]
            if _is_coordinated(intervening, last_ref[0], expected_cat):
                last_ref = (last_ref[0], ref_end_offset)
                continue

        clean_before = _clean_preceding_text(source.text[: token.start])
        word = _extract_last_word(clean_before)

        status = _match_category(word, expected_cat)
        if status is None:
            last_ref = (expected_cat, ref_end_offset)
            continue

        last_ref = None
        example = _suggest_example(expected_cat, target)

        if status == "page":
            explanation = "Page reference '\\pageref' must be preceded by a page noun (e.g. 'page' or 'Seite')."
            correction = f"Specify 'page' or 'Seite' before '\\pageref{{{target}}}'."
        elif status == "mismatch":
            explanation = f"Category noun '{word}' does not match prefix of referenced label '{target}'."
            correction = f"Change category noun to match '{target}' (e.g. '{example}')."
        else:
            explanation = "Reference must specify the category noun of the referenced object."
            correction = f"Specify the object type before the reference (e.g. '{example}')."

        yield source.finding(token.start, RULE.rule_id, explanation, correction)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate explicit reference categorization across all sources in the document."""
    for source in document.sources:
        yield from _check_source(source)


RULE = Rule(
    rule_id="TYPO-10",
    explanation="Reference must specify the category noun of the referenced object.",
    correction="Specify the object type before the reference (e.g. 'Figure~\\ref{...}' or 'Section~\\ref{...}').",
    passing_examples=(
        "See Figure~\\ref{fig:arch} for structural details.",
        "As shown in Section~\\ref{sec:methods} and Table~\\ref{tab:results}.",
        "Detailed in Figures~\\ref{fig:a} and~\\ref{fig:b} on page~\\pageref{fig:a}.",
    ),
    failing_examples=(
        "As seen in~\\ref{fig:arch}, the network converges.",
        "See Table~\\ref{fig:arch} for results.",
        "Details on \\pageref{fig:arch} describe the setup.",
    ),
    limits=(
        "Checks that \\ref commands are preceded by a category noun matching the referenced object's prefix "
        "(e.g. 'fig:' requires Figure/Abbildung, 'tab:' requires Table/Tabelle, 'sec:' requires Section/Abschnitt, "
        "'ch:' requires Chapter/Kapitel). Also checks that \\pageref is preceded by a page word ('page', 'Seite', "
        "'p.'). Coordinated references (e.g. 'Figures~\\ref{...} and~\\ref{...}') and numeric ranges are permitted. "
        "Commands with built-in categories (\\autoref, \\eqref, \\cref, \\Cref) and equation labels are excluded."
    ),
    evaluate=_evaluate,
)
