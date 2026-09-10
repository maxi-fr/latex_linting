from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source


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


def _collect_equation_labels(document: "Document") -> set[str]:
    """Collect all equation labels defined across the document."""
    labels: set[str] = set()
    for source in document.sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind == "command" and token.value == r"\label":
                target, _ = _extract_braced_argument(tokens, idx)
                if target and (target.startswith("eq:") or token.math == "display"):
                    labels.add(target)
    return labels


def _map_equation_tokens(
    sources: Sequence[Source],
    all_equation_labels: set[str],
) -> tuple[dict[tuple[str, int], str], dict[tuple[str, int], str]]:
    """Index label declarations and equation references by source location."""
    labels_at: dict[tuple[str, int], str] = {}
    refs_at: dict[tuple[str, int], str] = {}

    for source in sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind != "command":
                continue
            if token.value == r"\label":
                target, _ = _extract_braced_argument(tokens, idx)
                if target in all_equation_labels:
                    labels_at[(source.filename, token.start)] = target
            elif token.value in (r"\eqref", r"\ref") and token.math == "text":
                target, _ = _extract_braced_argument(tokens, idx)
                if target in all_equation_labels:
                    refs_at[(source.filename, token.start)] = target

    return labels_at, refs_at


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate chronological equation referencing across the document reading order."""
    all_equation_labels = _collect_equation_labels(document)
    if not all_equation_labels:
        return

    equation_labels_at, equation_refs_at = _map_equation_tokens(
        document.sources,
        all_equation_labels,
    )

    seen_labels: set[str] = set()
    for source, token in document.traverse():
        key = (source.filename, token.start)
        if key in equation_labels_at:
            seen_labels.add(equation_labels_at[key])
        if key in equation_refs_at:
            target = equation_refs_at[key]
            if target not in seen_labels:
                explanation = f"Forward reference to equation '{target}' before its definition."
                correction = (
                    f"Introduce equation '{target}' before referring to it, or move the reference after the equation."
                )
                yield source.finding(token.start, RULE.rule_id, explanation, correction)


RULE = Rule(
    rule_id="TYPO-11",
    explanation="Forward reference to equation before its definition.",
    correction="Introduce the equation before referring to it, or move the reference after the equation.",
    passing_examples=(
        (
            "\\begin{equation}\n"
            "\\label{eq:first}\n"
            "  a = b \\,.\n"
            "\\end{equation}\n"
            "As established in~\\eqref{eq:first}, the model holds."
        ),
        (
            "\\begin{equation}\n"
            "\\label{eq:model}\n"
            "  y = f(x) \\,.\n"
            "\\end{equation}\n"
            "Equation~\\eqref{eq:model} describes the transformation."
        ),
    ),
    failing_examples=(
        (
            "As will be shown in~\\eqref{eq:later}, the model holds.\n"
            "\\begin{equation}\n"
            "\\label{eq:later}\n"
            "  a = b \\,.\n"
            "\\end{equation}"
        ),
        (
            "We preview equation~\\eqref{eq:preview} before deriving it.\n"
            "\\begin{equation}\n"
            "\\label{eq:preview}\n"
            "  E = m \\cdot c^2 \\,.\n"
            "\\end{equation}"
        ),
    ),
    limits=(
        "Checks that equation references (\\eqref or \\ref with 'eq:' prefix or display math label) "
        "refer back chronologically to equations defined earlier in the document reading order. "
        "Equations defined later in the document tree are flagged as forward references. "
        "Undefined equations and non-equation references are excluded."
    ),
    evaluate=_evaluate,
)
