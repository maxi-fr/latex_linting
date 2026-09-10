from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.scanner import Token, scan
from latex_linting.source import Finding, Source

_NUMBERED_MATH_ENVIRONMENTS = frozenset(
    {
        "align",
        "alignat",
        "equation",
        "eqnarray",
        "flalign",
        "gather",
        "multline",
    }
)

_REFERENCE_COMMANDS = frozenset({r"\ref", r"\eqref", r"\autoref", r"\cref", r"\Cref"})


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


def _collect_document_references(document: "Document") -> set[str]:
    """Collect all label keys referenced by recognized citation and reference commands."""
    referenced: set[str] = set()
    for source in document.sources:
        tokens = scan(source.text)
        for idx, token in enumerate(tokens):
            if token.kind == "command" and token.value in _REFERENCE_COMMANDS:
                arg, _ = _extract_braced_argument(tokens, idx)
                if arg:
                    for part in arg.split(","):
                        cleaned = part.strip()
                        if cleaned:
                            referenced.add(cleaned)
    return referenced


def _collect_environment_labels(
    tokens: Sequence[Token],
    start_idx: int,
    env_name: str,
) -> tuple[list[tuple[Token, str]], int]:
    """Collect all label commands and targets inside a display math environment."""
    labels: list[tuple[Token, str]] = []
    env_depth = 1
    idx = start_idx
    while idx < len(tokens) and env_depth > 0:
        cur = tokens[idx]
        if cur.kind == "environment":
            cur_name = cur.value[cur.value.index("{") + 1 : -1]
            if cur.value.startswith(r"\begin") and cur_name == env_name:
                env_depth += 1
            elif cur.value.startswith(r"\end") and cur_name == env_name:
                env_depth -= 1
                if env_depth == 0:
                    return labels, idx + 1
        elif cur.kind == "command" and cur.value == r"\label":
            lbl_target, _ = _extract_braced_argument(tokens, idx)
            if lbl_target:
                labels.append((cur, lbl_target))
        idx += 1
    return labels, idx


def _check_source_equations(source: Source, referenced_labels: set[str]) -> Iterable[Finding]:
    """Scan a source file for labeled numbered equations lacking references in the document."""
    tokens = scan(source.text)
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind != "environment" or not token.value.startswith(r"\begin"):
            idx += 1
            continue

        name = token.value[token.value.index("{") + 1 : -1]
        if name not in _NUMBERED_MATH_ENVIRONMENTS:
            idx += 1
            continue

        labels_in_env, idx = _collect_environment_labels(tokens, idx + 1, name)

        for label_token, lbl_target in labels_in_env:
            if lbl_target not in referenced_labels:
                explanation = f"Numbered equation '{lbl_target}' is never referenced in the document."
                correction = (
                    f"Reference this equation using \\eqref{{{lbl_target}}}, "
                    "or use an unnumbered environment (e.g. 'equation*')."
                )
                yield source.finding(label_token.start, RULE.rule_id, explanation, correction)


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate numbered equations against recognized document-wide references."""
    referenced_labels = _collect_document_references(document)
    for source in document.sources:
        yield from _check_source_equations(source, referenced_labels)


RULE = Rule(
    rule_id="MATH-02",
    explanation="Numbered equation is never referenced in the document.",
    correction="Reference this equation using \\eqref{...}, or use an unnumbered environment (e.g. 'equation*').",
    passing_examples=(
        (
            "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:einstein}\n\\end{equation}\n"
            "As seen in~\\eqref{eq:einstein}, mass and energy are equivalent."
        ),
        "\\begin{equation*}\n  E = mc^2 \\,.\n\\end{equation*}",
        "\\[\n  x = y \\,.\n\\]",
    ),
    failing_examples=(
        "\\begin{equation}\n  E = mc^2 \\,.\n  \\label{eq:unused}\n\\end{equation}",
        "\\begin{align}\n  a &= b \\label{eq:unused} \\,.\n\\end{align}",
    ),
    limits=(
        "Evaluates labeled numbered display math environments (equation, align, gather, multline, "
        "alignat, flalign, eqnarray) against recognized references (\\ref, \\eqref, \\autoref, "
        "\\cref, \\Cref) collected across the entire document, including across included source files. "
        "Unreferenced labels are flagged at the \\label command. Unlabeled numbered equations are not "
        "flagged because the rule verifies equations through declared \\label commands; equations "
        "requiring references must declare a label. Unnumbered environments (starred forms, "
        "displaymath, \\[...\\], $$...$$) do not require references. References in comments or literal "
        "code do not count. Does not prohibit forward references (references appearing before the equation)."
    ),
    evaluate=_evaluate,
)
