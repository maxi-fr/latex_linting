import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_ABBREVIATIONS = (
    "Dr.",
    "Prof.",
    "cf.",
    "e.g.",
    "et al.",
    "i.e.",
    "vs.",
    "Fig.",
    "Tab.",
    "Sec.",
    "Eq.",
    "eq.",
    "Gl.",
    "gl.",
)

_REDUNDANT_WORD_PATTERN = re.compile(
    r"\b(?P<word>equation|eq\.|eq|Gleichung|Gl\.|Gl)\s*~?$",
    re.IGNORECASE,
)


def _skip_ignorable(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past whitespace and comments."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _skip_optional_bracket(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past optional bracket argument if present."""
    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.lstrip().startswith("["):
        while idx < len(tokens):
            if "]" in tokens[idx].value:
                return idx + 1
            idx += 1
    return idx


def _extract_braced_argument(tokens: Sequence[Token], cmd_idx: int) -> tuple[str, int]:
    """Extract braced argument text following a command, skipping comments and whitespace."""
    idx = _skip_ignorable(tokens, cmd_idx + 1)
    idx = _skip_ignorable(tokens, _skip_optional_bracket(tokens, idx))
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


def _collect_equation_labels(document: "Document") -> set[str]:
    """Collect labels defined inside display math environments across the document."""
    labels: set[str] = set()
    for source in document.sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind == "command" and token.value == r"\label" and token.math == "display":
                lbl, _ = _extract_braced_argument(tokens, idx)
                if lbl:
                    labels.add(lbl)
    return labels


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


def _is_sentence_start(source_text: str, word_start: int, word: str) -> bool:
    """Determine whether the word appears at the start of a sentence."""
    if not word[0].isupper():
        return False

    prefix = source_text[:word_start]
    if re.search(r"\n\s*\n\s*$", prefix):
        return True

    clean_prefix = _clean_preceding_text(prefix)
    if not clean_prefix:
        return True

    if clean_prefix.endswith("}") and re.search(
        r"\\(?:end\{[a-zA-Z*]+\}|chapter\*?\{[^}]*\}|section\*?\{[^}]*\})$",
        clean_prefix,
    ):
        return True

    stripped_quotes = clean_prefix.rstrip("\"'\u201d\u2019)")
    return (
        stripped_quotes.endswith((".", "?", "!"))
        and not stripped_quotes.endswith("..")
        and not stripped_quotes.endswith(_ABBREVIATIONS)
    )


def _check_redundant_word(source: Source, token: Token) -> tuple[Finding | None, bool]:
    """Check for redundant equation words preceding an equation reference command."""
    clean_before = _clean_preceding_text(source.text[: token.start])
    match = _REDUNDANT_WORD_PATTERN.search(clean_before)
    if not match:
        return None, False

    word = match.group("word")
    word_offset = clean_before.rfind(word, match.start("word"))
    if _is_sentence_start(source.text, word_offset, word):
        return None, True

    explanation = "Redundant equation wording before equation reference in running text."
    correction = (
        f"Omit '{word}' in running text (e.g. 'as shown in \\eqref{{...}}'), "
        "or write 'Equation' only at sentence start."
    )
    return source.finding(word_offset, RULE.rule_id, explanation, correction), False


def _check_ref_command(
    source: Source,
    tokens: Sequence[Token],
    idx: int,
    equation_labels: set[str],
    *,
    is_sentence_start: bool = False,
) -> Finding | None:
    r"""Check syntax of a \ref command used for an equation or parenthesized."""
    token = tokens[idx]
    clean_before = _clean_preceding_text(source.text[: token.start])
    target, end_idx = _extract_braced_argument(tokens, idx)
    after_text = source.text[tokens[end_idx - 1].end if end_idx > 0 else token.end :].lstrip()

    if clean_before.endswith("(") and after_text.startswith(")"):
        explanation = "Equation referenced using '(\\ref{...})'; '\\eqref' should be used instead."
        correction = f"Replace '(\\ref{{{target}}})' with '\\eqref{{{target}}}'."
        return source.finding(token.start, RULE.rule_id, explanation, correction)

    if (target.startswith("eq:") or target in equation_labels) and not is_sentence_start:
        explanation = "Equation referenced using '\\ref'; equations should be referenced using '\\eqref'."
        correction = f"Replace '\\ref{{{target}}}' with '\\eqref{{{target}}}'."
        return source.finding(token.start, RULE.rule_id, explanation, correction)

    return None


def _check_source_references(source: Source, equation_labels: set[str]) -> Iterable[Finding]:
    """Scan a source file for equation reference syntax violations and redundant wording."""
    tokens = scan(source.text)
    for idx, token in enumerate(tokens):
        if token.kind != "command" or token.math != "text" or token.value not in (r"\eqref", r"\ref"):
            continue

        redundant_finding, is_sentence_start = _check_redundant_word(source, token)
        if redundant_finding is not None:
            yield redundant_finding

        if token.value == r"\ref":
            ref_finding = _check_ref_command(
                source,
                tokens,
                idx,
                equation_labels,
                is_sentence_start=is_sentence_start,
            )
            if ref_finding is not None:
                yield ref_finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate equation reference syntax and redundant wording across the document."""
    equation_labels = _collect_equation_labels(document)
    for source in document.sources:
        yield from _check_source_references(source, equation_labels)


RULE = Rule(
    rule_id="MATH-03",
    explanation="Equation reference syntax or redundant wording in running text.",
    correction=(
        "Use '\\eqref{...}' without redundant words like 'equation' in running text; "
        "write 'Equation' only at sentence start."
    ),
    passing_examples=(
        "As shown in \\eqref{eq:model}, the error decreases.",
        "Equation~\\eqref{eq:model} describes the system dynamics.",
        "According to Section~\\ref{sec:methods}, the setup is complete.",
    ),
    failing_examples=(
        "As shown in equation~\\eqref{eq:model}, the error decreases.",
        "As shown in Eq.~\\eqref{eq:model}, the error decreases.",
        "As shown in \\ref{eq:model}, the error decreases.",
        "As shown in (\\ref{eq:model}), the error decreases.",
    ),
    limits=(
        "Detects redundant equation words ('equation', 'eq.', 'eq', 'Gleichung', 'Gl.', case-insensitive) "
        "immediately preceding \\eqref or \\ref in running text, except when capitalized at sentence start "
        "(e.g. 'Equation~\\eqref{...}'). Flags \\ref used with equation labels (prefix 'eq:' or labels "
        "defined in math environments) and parenthesized (\\ref{...}), recommending \\eqref{...}. "
        "Comments, literal code, and math mode are excluded."
    ),
    evaluate=_evaluate,
)
