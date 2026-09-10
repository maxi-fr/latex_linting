import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document, DocumentNode
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding

_SUPPORTED_HEADINGS = frozenset(
    {
        r"\chapter",
        r"\paragraph",
        r"\part",
        r"\section",
        r"\subparagraph",
        r"\subsection",
        r"\subsubsection",
    }
)

_MINOR_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "but",
        "by",
        "for",
        "from",
        "in",
        "into",
        "nor",
        "of",
        "on",
        "or",
        "over",
        "the",
        "to",
        "via",
        "with",
    }
)

_WORD_PATTERN = re.compile(r"\b[a-zA-Z]+(?:['\u2019][a-zA-Z]+)?(?:-[a-zA-Z]+(?:['\u2019][a-zA-Z]+)?)*\b")


def _skip_ignorable(tokens: Sequence[Token], idx: int) -> int:
    """Advance index over comments and whitespace text tokens."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _skip_star_and_bracket(tokens: Sequence[Token], idx: int) -> int:
    """Advance index over optional heading star and optional bracket arguments."""
    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.lstrip().startswith("*"):
        val = tokens[idx].value.lstrip()[1:].strip()
        idx = _skip_ignorable(tokens, idx + 1) if not val else idx + 1

    if idx < len(tokens) and tokens[idx].kind == "text" and tokens[idx].value.lstrip().startswith("["):
        while idx < len(tokens):
            if "]" in tokens[idx].value:
                idx += 1
                break
            idx += 1
        idx = _skip_ignorable(tokens, idx)

    return idx


def _extract_braced_tokens(tokens: Sequence[Token], idx: int) -> tuple[list[Token], int]:
    """Consume and return tokens inside balanced curly braces."""
    if idx >= len(tokens) or tokens[idx].kind != "brace" or tokens[idx].value != "{":
        return [], idx

    brace_depth = 1
    idx += 1
    heading_tokens: list[Token] = []
    while idx < len(tokens) and brace_depth > 0:
        t = tokens[idx]
        if t.kind == "brace":
            if t.value == "{":
                brace_depth += 1
            elif t.value == "}":
                brace_depth -= 1
        if brace_depth > 0:
            heading_tokens.append(t)
        idx += 1

    return heading_tokens, idx


def _extract_heading_tokens(tokens: Sequence[Token], start_idx: int) -> tuple[list[Token], int]:
    """Parse tokens within a heading's mandatory argument, skipping optional star and brackets."""
    idx = _skip_ignorable(tokens, start_idx)
    idx = _skip_star_and_bracket(tokens, idx)
    return _extract_braced_tokens(tokens, idx)


def _is_headline_case(words: Sequence[str]) -> bool:
    """Check whether a list of words follows American headline capitalization."""
    if not words:
        return True
    for i, word in enumerate(words):
        is_first = i == 0
        is_last = i == len(words) - 1
        parts = word.split("-")
        for j, part in enumerate(parts):
            if part.isupper():
                continue
            part_is_first = is_first and (j == 0)
            part_is_last = is_last and (j == len(parts) - 1)
            if part_is_first or part_is_last:
                if not part[0].isupper():
                    return False
            elif part.lower() in _MINOR_WORDS:
                if not part.islower():
                    return False
            elif not part[0].isupper():
                return False
    return True


def _iter_nodes(node: "DocumentNode") -> Iterable["DocumentNode"]:
    """Yield document nodes recursively in reading order."""
    yield node
    for _, child in node.children:
        yield from _iter_nodes(child)


def _headline_capitalization(document: "Document") -> Iterable[Finding]:
    """Report headings that do not use American headline capitalization."""
    for node in _iter_nodes(document.root_node):
        source = node.source
        tokens = node.tokens
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.kind == "command" and token.math == "text" and token.value in _SUPPORTED_HEADINGS:
                heading_tokens, next_idx = _extract_heading_tokens(tokens, idx + 1)
                words: list[str] = []
                for t in heading_tokens:
                    if t.kind == "text" and t.math == "text":
                        words.extend(m.group() for m in _WORD_PATTERN.finditer(t.value))
                if not _is_headline_case(words):
                    yield source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction)
                idx = next_idx
            else:
                idx += 1


RULE = Rule(
    rule_id="PROSE-04",
    explanation="Headings must use American headline capitalization.",
    correction=(
        "Capitalize the first, last, and major words; keep minor words "
        "(articles, conjunctions, short prepositions) lowercase unless first or last."
    ),
    passing_examples=(
        r"\chapter{A Really Awesome Thesis}",
        r"\section{Closed-Loop Deep Brain Stimulation}",
        r"\section{Methods and Tools}",
        r"\section{Optimization of $H_\infty$ Controllers}",
    ),
    failing_examples=(
        r"\section{Methods in machine learning}",
        r"\section{methods and Tools}",
        r"\section{Methods In Machine Learning}",
        r"\section{Closed-loop Systems}",
    ),
    limits=(
        r"Checks American headline capitalization on supported headings (\part, \chapter, "
        r"\section, \subsection, \subsubsection, \paragraph, \subparagraph, and starred forms). "
        "First and last words must be capitalized. Minor words (articles: a, an, the; "
        "coordinating conjunctions: and, but, or, nor, for; short prepositions: in, on, at, to, "
        "by, of, from, into, with, over, as, via) must be lowercase in interior positions. "
        "Hyphenated compound words have each component checked against these rules. "
        "All-uppercase acronyms (e.g. API, CNN, IAT) are permitted. Math ($...$) and commands "
        "inside headings are ignored. Findings attach to the heading command backslash."
    ),
    evaluate=_headline_capitalization,
)
