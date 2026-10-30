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
        r"\citealp",
        r"\citealt",
        r"\citeauthor",
        r"\citep",
        r"\citet",
        r"\citeyear",
        r"\footcite",
        r"\fullcite",
        r"\nocite",
        r"\parencite",
        r"\textcite",
        r"\Autocite",
        r"\Cite",
        r"\Citealp",
        r"\Citealt",
        r"\Citeauthor",
        r"\Citep",
        r"\Citet",
        r"\Parencite",
        r"\Textcite",
    }
)

_RESET_COMMANDS = frozenset(
    {
        r"\par",
        r"\item",
        r"\part",
        r"\chapter",
        r"\section",
        r"\subsection",
        r"\subsubsection",
        r"\paragraph",
        r"\subparagraph",
        r"\addchap",
        r"\addsec",
        r"\frontmatter",
        r"\mainmatter",
        r"\backmatter",
        r"\appendix",
        r"\clearpage",
        r"\cleardoublepage",
        r"\newpage",
        r"\pagebreak",
    }
)

_MATH_ENVIRONMENTS = frozenset(
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
        "split",
        "cases",
        "matrix",
        "pmatrix",
        "bmatrix",
        "vmatrix",
        "Vmatrix",
    }
)

_BLANK_LINE_RE = re.compile(r"(?:\r?\n)[ \t]*(?:\r?\n)")


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

    if arg_idx < len(tokens) and tokens[arg_idx].kind == "text" and tokens[arg_idx].value.startswith("*"):
        if tokens[arg_idx].value == "*":
            arg_idx += 1
        arg_idx = _skip_token_comments_and_spaces(tokens, arg_idx)

    while arg_idx < len(tokens) and tokens[arg_idx].kind == "text" and tokens[arg_idx].value.startswith("["):
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


def _is_reset_token(token: Token) -> bool:
    """Return True if token marks a paragraph break, heading, or non-math environment."""
    if token.kind == "text":
        return bool(_BLANK_LINE_RE.search(token.value))
    if token.kind == "command":
        return token.value in _RESET_COMMANDS
    if token.kind == "environment":
        name = token.value[token.value.index("{") + 1 : -1]
        return name not in _MATH_ENVIRONMENTS
    return False


def _evaluate_node(node: "DocumentNode") -> Iterable[Finding]:
    """Scan tokens in a single document node for consecutive duplicate citations."""
    source = node.source
    tokens = node.tokens
    idx = 0
    last_cite: tuple[Source, Token, frozenset[str]] | None = None

    while idx < len(tokens):
        token = tokens[idx]

        if _is_reset_token(token):
            last_cite = None
            idx += 1
            continue

        if token.kind == "command" and token.math == "text" and token.value in _CITATION_COMMANDS:
            keys, next_idx = _parse_citation_keys_at(tokens, idx + 1)
            if not keys:
                idx = max(next_idx, idx + 1)
                continue

            key_set = frozenset(keys)
            if last_cite is not None:
                prev_source, prev_token, prev_key_set = last_cite
                if key_set == prev_key_set:
                    keys_str = ", ".join(sorted(prev_key_set))
                    explanation = (
                        f"Redundant consecutive citation of '{keys_str}' without an intervening reference; "
                        "the earlier citation is redundant because the subsequent citation is sufficient."
                    )
                    yield prev_source.finding(prev_token.start, RULE.rule_id, explanation, RULE.correction)

            last_cite = (source, token, key_set)
            idx = max(next_idx, idx + 1)
            continue

        idx += 1


def _iter_nodes(node: "DocumentNode") -> Iterable["DocumentNode"]:
    """Yield a document node and all of its recursively included child nodes."""
    yield node
    for _, child in node.children:
        yield from _iter_nodes(child)


def _consecutive_citations(document: "Document") -> Iterable[Finding]:
    """Report redundant consecutive citations of the same reference in the same paragraph."""
    if document.root_node.source.filename.endswith(".bib"):
        return ()

    for node in _iter_nodes(document.root_node):
        yield from _evaluate_node(node)


RULE = Rule(
    rule_id="CITE-07",
    explanation=(
        "Consecutive citation of the same reference without an intervening reference; "
        "the earlier citation is redundant because the subsequent citation is sufficient."
    ),
    correction="Remove the redundant earlier citation or cite only once at the end of the claim.",
    passing_examples=(
        r"Sentence one discusses the technique~\cite{vaswani2017}. Sentence two discusses alternative models~\cite{devlin2018}. Sentence three builds on the first~\cite{vaswani2017}.",
        r"The initial concept~\cite{vaswani2017} was extended to language models~\cite{devlin2018}. Later experiments confirmed the gains~\cite{vaswani2017}.",
        "The method converges linearly in convex settings~\\cite{vaswani2017}.\n\nIn nonconvex settings, stability depends on step size~\\cite{vaswani2017}.",
    ),
    failing_examples=(
        r"Sentence one establishes the foundational architecture~\cite{vaswani2017}. Sentence two details its performance gains~\cite{vaswani2017}.",
        r"The primary model~\cite{devlin2018, vaswani2017} was trained first. Subsequent evaluation confirmed the architecture~\cite{devlin2018, vaswani2017}.",
        r"The initial concept~\cite{vaswani2017} was applied to translation~\cite{vaswani2017}.",
    ),
    limits=(
        r"Detects consecutive identical citations (\cite, \citep, \citet, \autocite, \parencite, "
        r"\textcite, \footcite, \fullcite, \nocite, \citeauthor, \citeyear, and capitalized variants) "
        r"sharing the exact same citation key or set of keys in running text within the same paragraph. "
        r"Resets on paragraph breaks (blank lines or \par), headings, division commands, page breaks, "
        r"and non-math environment boundaries. Flags the earlier citation command."
    ),
    evaluate=_consecutive_citations,
    enabled_by_default=True,
    severity="error",
)
