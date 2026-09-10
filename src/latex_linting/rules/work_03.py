from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding, Source

_FORBIDDEN_OPTIONS = frozenset({"draft", "oneside", "nohyperref"})
_FALSE_VALUES = frozenset({"false", "off", "no"})


def _skip_braces(text: str, start: int) -> int:
    """Skip over matching curly braces, accounting for nested braces and comments."""
    depth = 1
    idx = start + 1
    while idx < len(text) and depth > 0:
        char = text[idx]
        if char == "%":
            idx = text.find("\n", idx)
            if idx == -1:
                return len(text)
            idx += 1
        elif char == "{":
            depth += 1
            idx += 1
        elif char == "}":
            depth -= 1
            idx += 1
        else:
            idx += 1
    return idx


def _find_opening_bracket(text: str, start: int) -> int | None:
    """Locate the opening bracket following documentclass, skipping comments."""
    idx = start
    while idx < len(text):
        char = text[idx]
        if char.isspace():
            idx += 1
        elif char == "%":
            idx = text.find("\n", idx)
            if idx == -1:
                return None
            idx += 1
        elif char == "[":
            return idx
        else:
            return None
    return None


def _find_closing_bracket(text: str, start: int) -> int | None:
    """Locate the matching closing bracket, skipping braces and comments."""
    depth = 1
    idx = start
    while idx < len(text) and depth > 0:
        char = text[idx]
        if char == "%":
            idx = text.find("\n", idx)
            if idx == -1:
                return None
            idx += 1
        elif char == "{":
            idx = _skip_braces(text, idx)
        elif char == "[":
            depth += 1
            idx += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return idx
            idx += 1
        else:
            idx += 1
    return None


def _find_bracket_options(text: str, start: int) -> tuple[int, int] | None:
    """Locate the bracket span following documentclass, skipping comments."""
    open_idx = _find_opening_bracket(text, start)
    if open_idx is None:
        return None
    close_idx = _find_closing_bracket(text, open_idx + 1)
    if close_idx is None:
        return None
    return open_idx + 1, close_idx


def _parse_option_items(text: str, start: int, end: int) -> list[tuple[str, int]]:
    """Return comma-separated option items with their start offsets in text."""
    items: list[tuple[str, int]] = []
    item_start = start
    idx = start
    while idx < end:
        char = text[idx]
        if char == "%":
            idx = text.find("\n", idx)
            if idx == -1 or idx >= end:
                break
            idx += 1
        elif char == "{":
            idx = _skip_braces(text, idx)
        elif char == ",":
            items.append((text[item_start:idx], item_start))
            idx += 1
            item_start = idx
        else:
            idx += 1
    if item_start < end:
        items.append((text[item_start:end], item_start))
    return items


def _forbidden_options_in_source(source: Source) -> Iterable[Finding]:
    """Find forbidden document-class options within a single source file."""
    text = source.text
    offset = 0
    cmd = r"\documentclass"
    while offset < len(text):
        idx = text.find(cmd, offset)
        if idx == -1:
            break
        cmd_end = idx + len(cmd)
        if cmd_end < len(text) and text[cmd_end].isalpha():
            offset = cmd_end
            continue
        bracket_span = _find_bracket_options(text, cmd_end)
        if bracket_span is not None:
            b_start, b_end = bracket_span
            for raw_item, raw_start in _parse_option_items(text, b_start, b_end):
                clean = raw_item
                if "%" in clean:
                    clean = clean[: clean.index("%")]
                stripped = clean.strip()
                if not stripped:
                    continue
                leading = len(clean) - len(clean.lstrip())
                opt_offset = raw_start + leading
                key, _, val = stripped.partition("=")
                key = key.strip()
                val = val.strip() if val else None
                if key in _FORBIDDEN_OPTIONS:
                    if val is not None and val.lower() in _FALSE_VALUES:
                        continue
                    key_offset = opt_offset + clean.lstrip().index(key)
                    explanation = (
                        f"Forbidden document-class option '{key}'; "
                        "final thesis submission requires two-sided layout and no draft or nohyperref options."
                    )
                    correction = f"Remove the '{key}' option from \\documentclass."
                    yield source.finding(key_offset, RULE.rule_id, explanation, correction)
        offset = cmd_end


def _forbidden_options(document: "Document") -> Iterable[Finding]:
    """Report forbidden document-class options across the loaded document."""
    for source in document.sources:
        yield from _forbidden_options_in_source(source)


RULE = Rule(
    rule_id="WORK-03",
    explanation="Forbidden document-class option; final submission requires two-sided layout without draft, oneside, or nohyperref options.",
    correction=r"Remove draft, oneside, or nohyperref options from \documentclass and configure two-sided printing.",
    passing_examples=(
        r"\documentclass[12pt,twoside,a4paper]{report}",
        r"\documentclass{scrreprt}",
    ),
    failing_examples=(
        r"\documentclass[draft]{report}",
        r"\documentclass[12pt,oneside]{book}",
        r"\documentclass[nohyperref]{scrreprt}",
    ),
    limits=(
        r"Detects explicitly specified forbidden options (draft, oneside, nohyperref) in "
        r"\documentclass[...] brackets. Does not establish class defaults, effective page dimensions, "
        "or complete submission compliance. Comments within options are ignored. "
        "Does not parse documentclass files or evaluate TeX conditionals."
    ),
    evaluate=_forbidden_options,
)
