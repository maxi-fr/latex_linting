from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_DISPLAY_ENVIRONMENTS = frozenset(
    {
        "displaymath",
        "equation",
        "equation*",
        "align",
        "align*",
        "alignat",
        "alignat*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "flalign",
        "flalign*",
        "eqnarray",
        "eqnarray*",
    }
)

_TERMINAL_PUNCTUATION = frozenset({".", ",", ";", ":", "!", "?"})


def _is_display_open(token: Token) -> str | None:
    """Return the display environment or delimiter name if token opens display math."""
    if token.kind == "command" and token.value == r"\[":
        return r"\]"
    if token.kind == "delimiter" and token.value == "$$":
        return "$$"
    if token.kind == "environment" and token.value.startswith(r"\begin"):
        name = token.value[token.value.index("{") + 1 : -1]
        if name in _DISPLAY_ENVIRONMENTS:
            return r"\end{" + name + "}"
    return None


def _trim_trailing_tokens(inner_tokens: list[Token]) -> int:
    """Return the index of the last non-ignorable token before display math close."""
    idx = len(inner_tokens) - 1
    while idx >= 0:
        token = inner_tokens[idx]
        if token.kind == "comment" or (token.kind == "text" and token.value.isspace()):
            idx -= 1
            continue
        if token.kind == "command" and token.value in {r"\notag", r"\nonumber"}:
            idx -= 1
            continue
        if token.kind == "command" and token.value == r"\\":
            idx -= 1
            continue
        if token.kind == "brace" and token.value == "}":
            brace_depth = 1
            scan_idx = idx - 1
            while scan_idx >= 0 and brace_depth > 0:
                cur = inner_tokens[scan_idx]
                if cur.kind == "brace":
                    brace_depth += 1 if cur.value == "}" else -1
                scan_idx -= 1
            lookback = scan_idx
            while lookback >= 0 and (
                inner_tokens[lookback].kind == "comment"
                or (inner_tokens[lookback].kind == "text" and inner_tokens[lookback].value.isspace())
            ):
                lookback -= 1
            if lookback >= 0 and inner_tokens[lookback].kind == "command" and inner_tokens[lookback].value == r"\label":
                idx = lookback - 1
                continue
        break
    return idx


def _check_terminal_punctuation(inner_tokens: list[Token]) -> bool:
    """Return True if the equation ends with terminal punctuation preceded by thin space."""
    idx = _trim_trailing_tokens(inner_tokens)
    if idx < 0:
        return False

    token = inner_tokens[idx]
    if token.kind != "text":
        return False

    val = token.value.rstrip()
    if not val or val[-1] not in _TERMINAL_PUNCTUATION:
        return False

    before_punct = val[:-1].rstrip()
    if before_punct:
        return False

    prev_idx = idx - 1
    while prev_idx >= 0 and (
        inner_tokens[prev_idx].kind == "comment"
        or (inner_tokens[prev_idx].kind == "text" and inner_tokens[prev_idx].value.isspace())
    ):
        prev_idx -= 1

    if prev_idx < 0:
        return False

    prev_token = inner_tokens[prev_idx]
    return prev_token.kind == "command" and prev_token.value == r"\,"


def _check_source_display_math(source: Source) -> Iterable[Finding]:
    """Scan a single source for displayed math lacking terminal punctuation or thin spacing."""
    tokens = scan(source.text)
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        close_target = _is_display_open(token)
        if close_target is None:
            idx += 1
            continue

        inner_tokens: list[Token] = []
        close_token: Token | None = None
        idx += 1
        while idx < len(tokens):
            cur = tokens[idx]
            if (
                close_target in {r"\]", "$$"} and cur.kind in {"command", "delimiter"} and cur.value == close_target
            ) or (close_target.startswith(r"\end") and cur.kind == "environment" and cur.value == close_target):
                close_token = cur
                idx += 1
                break
            inner_tokens.append(cur)
            idx += 1

        if close_token is not None and not _check_terminal_punctuation(inner_tokens):
            yield source.finding(close_token.start, RULE.rule_id, RULE.explanation, RULE.correction)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report displayed math lacking terminal punctuation and thin spacing across the document."""
    for source in document.sources:
        yield from _check_source_display_math(source)


RULE = Rule(
    rule_id="MATH-01",
    explanation=r"Displayed math must terminate with punctuation preceded by a thin space (\,).",
    correction=r"Add terminal punctuation preceded by a thin space (e.g. \,, or \,.) before closing the displayed math.",
    passing_examples=(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}",
        "\\begin{align}\n  a &= b \\\\\n  c &= d \\,.\n\\end{align}",
        "\\[\n  x = y \\,.\n\\]",
    ),
    failing_examples=(
        "\\begin{equation}\n  E = mc^2\n\\end{equation}",
        "\\begin{equation}\n  E = mc^2.\n\\end{equation}",
        "\\[\n  x = y\n\\]",
    ),
    limits=(
        "Checks terminal punctuation (., ,, ;, :, !, ?) and preceding thin space (\\,) in supported "
        "displayed-math environments (equation, align, gather, multline, alipgnat, flalign, eqnarray, "
        "their starred forms, displaymath, \\[...\\], and $$...$$). Multiline equations are checked at "
        "the final line before closing. Trailing labels, comments, whitespace, and line breaks (\\\\) "
        "are ignored. Reports the closing delimiter or environment command. Does not verify grammatical "
        "appropriateness of the chosen punctuation."
    ),
    evaluate=_evaluate,
)
