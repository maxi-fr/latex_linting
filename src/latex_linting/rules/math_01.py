import re
from collections.abc import Iterable, Sequence
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
_INNER_DISPLAY_ENVIRONMENTS = frozenset(
    {
        "aligned",
        "split",
        "gathered",
        "alignedat",
        "cases",
        "cases*",
        "dcases",
        "dcases*",
        "rcases",
        "rcases*",
        "drcases",
        "drcases*",
    }
)
_CONTINUATION_PATTERN = re.compile(
    r"^(?:where|with|so\s+that|such\s+that|in\s+which|and|for|which|as|since|if|when|or|provided|that\s+is)\b"
)
_HEADING_COMMANDS = frozenset(
    {
        r"\part",
        r"\chapter",
        r"\section",
        r"\subsection",
        r"\subsubsection",
        r"\paragraph",
        r"\subparagraph",
        r"\addchap",
        r"\addsec",
    }
)


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


def _find_matching_begin(inner_tokens: list[Token], end_idx: int, env_name: str) -> int:
    """Return the index of the matching begin environment token, or -1 if unmatched."""
    depth = 1
    scan_idx = end_idx - 1
    while scan_idx >= 0 and depth > 0:
        cur = inner_tokens[scan_idx]
        if cur.kind == "environment":
            cur_name = cur.value[cur.value.index("{") + 1 : -1]
            if cur_name == env_name:
                if cur.value.startswith(r"\end"):
                    depth += 1
                elif cur.value.startswith(r"\begin"):
                    depth -= 1
        scan_idx -= 1
    return scan_idx + 1 if depth == 0 else -1


def _find_terminal_token(inner_tokens: list[Token]) -> int:
    """Return the index of the terminal token candidate, unwrapping supported inner environments."""
    idx = _trim_trailing_tokens(inner_tokens)
    while idx >= 0:
        token = inner_tokens[idx]
        if token.kind == "environment" and token.value.startswith(r"\end"):
            env_name = token.value[token.value.index("{") + 1 : -1]
            if env_name in _INNER_DISPLAY_ENVIRONMENTS:
                begin_idx = _find_matching_begin(inner_tokens, idx, env_name)
                if begin_idx < 0:
                    return -1
                trimmed = _trim_trailing_tokens(inner_tokens[:idx])
                if trimmed <= begin_idx:
                    return -1
                idx = trimmed
                continue
        break
    return idx


def _skip_label(tokens: Sequence[Token], idx: int) -> int:
    r"""Advance index past \label command and its argument."""
    cur = idx + 1
    while cur < len(tokens) and (
        tokens[cur].kind == "comment" or (tokens[cur].kind == "text" and tokens[cur].value.isspace())
    ):
        cur += 1
    if cur < len(tokens) and tokens[cur].kind == "text" and tokens[cur].value.lstrip().startswith("["):
        while cur < len(tokens):
            if "]" in tokens[cur].value:
                cur += 1
                break
            cur += 1
        while cur < len(tokens) and (
            tokens[cur].kind == "comment" or (tokens[cur].kind == "text" and tokens[cur].value.isspace())
        ):
            cur += 1
    if cur < len(tokens) and tokens[cur].kind == "brace" and tokens[cur].value == "{":
        brace_depth = 1
        cur += 1
        while cur < len(tokens) and brace_depth > 0:
            if tokens[cur].kind == "brace":
                brace_depth += 1 if tokens[cur].value == "{" else -1
            cur += 1
    return cur


def _skip_ignorable_following(tokens: Sequence[Token], start_idx: int) -> tuple[int, bool]:
    """Advance index past comments, whitespace, labels, and track paragraph commands."""
    idx = start_idx
    has_par = False
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind == "comment" or (token.kind == "text" and token.value.isspace()):
            idx += 1
        elif token.kind == "command" and token.value == r"\label":
            idx = _skip_label(tokens, idx)
        elif token.kind == "command" and token.value == r"\noindent":
            idx += 1
        elif token.kind == "command" and token.value == r"\par":
            has_par = True
            idx += 1
        else:
            break
    return idx, has_par


def _inspect_following_text(
    source: Source,
    tokens: Sequence[Token],
    start_idx: int,
    close_end: int,
) -> tuple[str | None, bool, bool]:
    """Inspect text following display math for continuation, paragraph break, or heading."""
    cur_idx, has_par = _skip_ignorable_following(tokens, start_idx)
    if cur_idx >= len(tokens):
        return None, False, False

    token = tokens[cur_idx]
    if token.value.startswith(r"\end{document}") or (token.value.startswith(r"\end") and "document" in token.value):
        return None, False, False

    if token.kind == "text":
        val = token.value.lstrip()
        text_start = token.start + (len(token.value) - len(val))
    else:
        val = token.value
        text_start = token.start

    has_par_break = has_par or bool(re.search(r"(?:\r?\n)[ \t]*(?:\r?\n)", source.text[close_end:text_start]))
    if token.kind == "command" and token.value in _HEADING_COMMANDS:
        return None, has_par_break, True

    return val, has_par_break, False


def _get_terminal_punctuation(inner_tokens: list[Token]) -> str | None:
    """Return the terminal punctuation character if preceded by thin space, else None."""
    idx = _find_terminal_token(inner_tokens)
    if idx < 0:
        return None

    token = inner_tokens[idx]
    if token.kind != "text":
        return None

    val = token.value.rstrip()
    if not val or val[-1] not in _TERMINAL_PUNCTUATION:
        return None

    before_punct = val[:-1].rstrip()
    if before_punct:
        return None

    prev_idx = idx - 1
    while prev_idx >= 0 and (
        inner_tokens[prev_idx].kind == "comment"
        or (inner_tokens[prev_idx].kind == "text" and inner_tokens[prev_idx].value.isspace())
    ):
        prev_idx -= 1

    if prev_idx < 0:
        return None

    prev_token = inner_tokens[prev_idx]
    return val[-1] if prev_token.kind == "command" and prev_token.value == r"\," else None


def _check_continuation(
    source: Source,
    tokens: Sequence[Token],
    close_token: Token,
    idx: int,
    terminal_punct: str,
) -> Finding | None:
    """Check sentence continuation grammar after displayed math."""
    following_val, has_par, is_heading = _inspect_following_text(source, tokens, idx, close_token.end)

    if terminal_punct == "." and following_val is not None and _CONTINUATION_PATTERN.match(following_val):
        explanation = "Displayed math ends with a period, but is followed by a sentence continuation."
        correction = "Replace '\\,.' with '\\,,' before closing the displayed math."
        return source.finding(close_token.start, RULE.rule_id, explanation, correction)

    if terminal_punct == ",":
        if is_heading:
            explanation = "Displayed math ends with a comma, but is followed by a heading."
            correction = "Replace '\\,,' with '\\,.' before closing the displayed math."
            return source.finding(close_token.start, RULE.rule_id, explanation, correction)
        if following_val is not None and has_par:
            explanation = "Displayed math ends with a comma, but is followed by a new paragraph."
            correction = "Replace '\\,,' with '\\,.' before closing the displayed math."
            return source.finding(close_token.start, RULE.rule_id, explanation, correction)
        if following_val is not None:
            clean_val = following_val.lstrip("\"'`\u201c\u2018")
            if clean_val and clean_val[0].isupper():
                explanation = "Displayed math ends with a comma, but is followed by a new capitalized sentence."
                correction = "Replace '\\,,' with '\\,.' before closing the displayed math."
                return source.finding(close_token.start, RULE.rule_id, explanation, correction)

    return None


def _check_source_display_math(source: Source) -> Iterable[Finding]:
    """Scan a single source for displayed math lacking punctuation or violating continuation grammar."""
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

        if close_token is None:
            continue

        terminal_punct = _get_terminal_punctuation(inner_tokens)
        if terminal_punct is None:
            yield source.finding(close_token.start, RULE.rule_id, RULE.explanation, RULE.correction)
            continue

        finding = _check_continuation(source, tokens, close_token, idx, terminal_punct)
        if finding is not None:
            yield finding


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report displayed math punctuation and continuation violations across the document."""
    for source in document.sources:
        yield from _check_source_display_math(source)


RULE = Rule(
    rule_id="MATH-01",
    explanation=r"Displayed math must terminate with punctuation preceded by a thin space (\,).",
    correction=r"Add terminal punctuation preceded by a thin space (e.g. \,, or \,.) before closing the displayed math.",
    passing_examples=(
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}",
        "\\begin{equation}\n  a = b \\,,\n\\end{equation}\nwhere $a$ and $b$ are constants.",
        "\\begin{align}\n  a &= b \\\\\n  c &= d \\,.\n\\end{align}",
        "\\[\n  x = y \\,.\n\\]",
    ),
    failing_examples=(
        "\\begin{equation}\n  E = mc^2\n\\end{equation}",
        "\\begin{equation}\n  E = mc^2.\n\\end{equation}",
        "\\begin{equation}\n  E = mc^2 \\,.\n\\end{equation}\nwhere $m$ is mass.",
        "\\begin{equation}\n  a = b \\,,\n\\end{equation}\nThis defines our model.",
        "\\[\n  x = y\n\\]",
    ),
    limits=(
        "Checks terminal punctuation (., ,, ;, :, !, ?) and preceding thin space (\\,) in supported "
        "displayed-math environments (equation, align, gather, multline, alignat, flalign, eqnarray, "
        "their starred forms, displaymath, \\[...\\], and $$...$$). Multiline equations are checked at "
        "the final line before closing. Trailing labels, comments, whitespace, and line breaks (\\\\) "
        "are ignored. Inner alignment environments (e.g. aligned, split, gathered, alignat, cases) are "
        "checked at their terminal position. Reports the closing delimiter or environment command. "
        "Verifies sentence continuation grammar: equations ending in a period must not be immediately "
        "followed by lowercase continuation words (e.g. 'where', 'with', 'so that', 'and', 'for'), and "
        "equations ending in a comma must not be followed by a new capitalized sentence, new paragraph, "
        "or heading."
    ),
    evaluate=_evaluate,
)
