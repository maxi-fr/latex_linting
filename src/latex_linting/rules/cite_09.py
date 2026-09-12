import re
from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document, DocumentNode
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token
from latex_linting.source import Finding, Source

_CITATION_COMMANDS = frozenset(
    {
        r"\autocite",
        r"\cite",
        r"\citeauthor",
        r"\citep",
        r"\citet",
        r"\citeyear",
        r"\footcite",
        r"\fullcite",
        r"\nocite",
        r"\parencite",
        r"\textcite",
    }
)

_CITE_CHECKED_RE = re.compile(r"%\s*cite-checked\s*:\s*(.+?)\s*$")


def _skip_token_comments_and_spaces(tokens: Sequence[Token], idx: int) -> int:
    """Advance index past comment tokens and whitespace text tokens."""
    while idx < len(tokens) and (
        tokens[idx].kind == "comment" or (tokens[idx].kind == "text" and tokens[idx].value.isspace())
    ):
        idx += 1
    return idx


def _parse_citation_keys_at(tokens: Sequence[Token], start_idx: int) -> tuple[list[str], int]:
    """Parse citation keys from tokens following a citation command."""
    arg_idx = _skip_token_comments_and_spaces(tokens, start_idx)
    if arg_idx < len(tokens) and tokens[arg_idx].kind == "text" and tokens[arg_idx].value.startswith("["):
        bracket_depth = 0
        while arg_idx < len(tokens):
            val = tokens[arg_idx].value
            bracket_depth += val.count("[") - val.count("]")
            arg_idx += 1
            if bracket_depth <= 0:
                break
        arg_idx = _skip_token_comments_and_spaces(tokens, arg_idx)

    if arg_idx >= len(tokens) or tokens[arg_idx].kind != "brace" or tokens[arg_idx].value != "{":
        return [], arg_idx + 1

    brace_depth = 1
    content_idx = arg_idx + 1
    keys_parts: list[str] = []
    while content_idx < len(tokens) and brace_depth > 0:
        cur = tokens[content_idx]
        if cur.kind == "brace":
            brace_depth += 1 if cur.value == "{" else -1
        if brace_depth > 0 and cur.kind != "comment":
            keys_parts.append(cur.value)
        content_idx += 1

    raw_keys = "".join(keys_parts)
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    return keys, content_idx


def _parse_comment_status(line_text: str, key: str) -> str | None:
    """Extract verification status for a key from a trailing cite-checked comment."""
    match = _CITE_CHECKED_RE.search(line_text)
    if not match:
        return None
    comment_body = match.group(1).strip()
    if "=" in comment_body:
        pairs = [p.strip() for p in comment_body.split(",") if p.strip()]
        for pair in pairs:
            if "=" in pair:
                k, v = pair.split("=", 1)
                if k.strip() == key:
                    return v.strip()
        return None
    return comment_body


def _iter_nodes(node: "DocumentNode") -> Iterable["DocumentNode"]:
    """Yield a document node and all of its recursively included child nodes."""
    yield node
    for _, child in node.children:
        yield from _iter_nodes(child)


def _find_unmarked_keys(
    keys: Sequence[str],
    line_text: str,
    closing_line_text: str,
) -> list[str]:
    """Identify citation keys lacking a trailing cite-checked status."""
    unmarked: list[str] = []
    for k in keys:
        status = _parse_comment_status(line_text, k)
        if status is None and closing_line_text:
            status = _parse_comment_status(closing_line_text, k)
        if status is None:
            unmarked.append(k)
    return unmarked


def _evaluate_citation_token(
    source: Source,
    tokens: Sequence[Token],
    idx: int,
) -> tuple[Finding | None, int]:
    """Evaluate a citation token at index and return any finding and next token index."""
    token = tokens[idx]
    keys, next_idx = _parse_citation_keys_at(tokens, idx + 1)
    line = source.line_number(token.start)
    line_start = source.offset_of(line, 1)
    line_end = source.text.find("\n", line_start)
    line_text = source.text[line_start : len(source.text) if line_end == -1 else line_end].rstrip("\r")

    closing_line = source.line_number(tokens[next_idx - 1].end - 1) if next_idx > idx + 1 else line
    closing_line_text = ""
    if closing_line != line:
        c_start = source.offset_of(closing_line, 1)
        c_end = source.text.find("\n", c_start)
        closing_line_text = source.text[c_start : len(source.text) if c_end == -1 else c_end].rstrip("\r")

    if not keys:
        status = _parse_comment_status(line_text, "") or (
            _parse_comment_status(closing_line_text, "") if closing_line_text else None
        )
        if status is None:
            return source.finding(token.start, RULE.rule_id, RULE.explanation, RULE.correction), next_idx
        return None, next_idx

    unmarked = _find_unmarked_keys(keys, line_text, closing_line_text)
    if not unmarked:
        return None, next_idx

    if len(unmarked) == 1:
        explanation = f"Citation '{unmarked[0]}' has not been marked with a '% cite-checked:' comment."
    else:
        formatted = ", ".join(f"'{k}'" for k in unmarked)
        explanation = f"Citations {formatted} have not been marked with a '% cite-checked:' comment."
    return source.finding(token.start, RULE.rule_id, explanation, RULE.correction), next_idx


def _evaluate_node(node: "DocumentNode") -> Iterable[Finding]:
    """Scan tokens of a single node and yield findings for unmarked citations."""
    source = node.source
    tokens = node.tokens
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind != "command" or token.math != "text" or token.value not in _CITATION_COMMANDS:
            idx += 1
            continue

        finding, next_idx = _evaluate_citation_token(source, tokens, idx)
        if finding is not None:
            yield finding
        idx = max(next_idx, idx + 1)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Report citation commands lacking a trailing % cite-checked: comment."""
    for node in _iter_nodes(document.root_node):
        yield from _evaluate_node(node)


RULE = Rule(
    rule_id="CITE-09",
    explanation="In-text citation has not been marked with a '% cite-checked:' comment.",
    correction="Add a trailing '% cite-checked: SUPPORTED' (or appropriate status) comment to the citation line.",
    passing_examples=(
        r"Recent advances demonstrate linear convergence~\cite{smith2020}. % cite-checked: SUPPORTED",
        r"Several algorithms exist~\citep{smith2020, doe2021}. % cite-checked: smith2020=SUPPORTED, doe2021=NOT_FOUND",
        r"The system reaches 99\% accuracy~\cite{doe2021}. % cite-checked: CONTRADICTED",
    ),
    failing_examples=(
        r"Recent advances demonstrate linear convergence~\cite{smith2020}.",
        r"Several algorithms exist~\citep{smith2020, doe2021}. % cite-checked: smith2020=SUPPORTED",
        r"According to~\citet{smith2020}, the bounds hold.",
    ),
    limits=(
        r"Detects recognized citation commands (\cite, \citep, \citet, \autocite, \parencite, "
        r"\textcite, \footcite, \fullcite, \nocite, \citeauthor, \citeyear) in text mode lacking a "
        r"'% cite-checked:' trailing comment. Multi-key citations require every key to be accounted for "
        r"(e.g. '% cite-checked: key1=SUPPORTED, key2=NOT_FOUND' or a shared verdict). "
        r"Off by default; activate with '--rule CITE-09' or '--enable CITE-09'. "
        r"Does not evaluate factual truth of cited sources."
    ),
    evaluate=_evaluate,
    enabled_by_default=False,
)
