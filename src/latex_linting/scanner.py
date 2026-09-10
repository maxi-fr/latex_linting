import re
from dataclasses import dataclass, replace
from typing import Literal, TypeAlias

MathContext: TypeAlias = Literal["text", "inline", "display"]

_LEXEME = re.compile(
    r"(?P<comment>%[^\r\n]*)"
    r"|(?P<environment>\\(?:begin|end)\s*\{[a-zA-Z*]+\})"
    r"|(?P<command>\\(?:[a-zA-Z]+|[^\r\n]))"
    r"|(?P<delimiter>\$\$?)"
    r"|(?P<brace>[{}])"
    r"|(?P<text>[^\\%${}]+|\\)"
)
_LITERAL_ENVIRONMENTS = frozenset({"verbatim", "verbatim*", "lstlisting", "minted"})
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


@dataclass(frozen=True)
class Token:
    """Retain a lexical item's source span and surrounding math context."""

    kind: str
    value: str
    start: int
    end: int
    math: MathContext = "text"


def _verb_end(text: str, start: int) -> int:
    """Consume a verb delimiter and body, stopping at a line end if unclosed."""
    if start < len(text) and text[start] == "*":
        start += 1
    if start == len(text) or text[start].isspace():
        return start
    end = start + 1
    while end < len(text) and text[end] not in (text[start], "\r", "\n"):
        end += 1
    return end + 1 if end < len(text) and text[end] == text[start] else end


def _read_token(text: str, offset: int) -> Token:
    """Read one lexical item, consuming literal bodies as opaque source spans."""
    match = _LEXEME.match(text, offset)
    if match is None or match.lastgroup is None:
        msg = f"Cannot scan source at offset {offset}"
        raise ValueError(msg)
    kind, value, end = match.lastgroup, match.group(), match.end()
    if kind == "command" and value == r"\verb":
        kind, end = "literal", _verb_end(text, end)
    elif kind == "environment":
        name = value[value.index("{") + 1 : -1]
        if value.startswith(r"\begin") and name in _LITERAL_ENVIRONMENTS:
            closing = re.search(r"\\end\s*\{" + re.escape(name) + r"\}", text[end:])
            kind, end = "literal", end + closing.end() if closing else len(text)
    return Token(kind, text[offset:end], offset, end)


def _math_transition(token: Token, stack: list[tuple[str, MathContext]]) -> None:
    """Enter and leave supported math delimiters without inspecting literal text."""
    value = token.value
    if token.kind == "environment":
        name = value[value.index("{") + 1 : -1]
        value = ("begin:" if value.startswith(r"\begin") else "end:") + name
        if value.startswith("begin:") and (name == "math" or name in _DISPLAY_ENVIRONMENTS):
            stack.append(("end:" + name, "inline" if name == "math" else "display"))
            return
    if stack and value == stack[-1][0]:
        stack.pop()
    elif token.kind in {"delimiter", "command"}:
        opening: dict[str, tuple[str, MathContext]] = {
            "$": ("$", "inline"),
            "$$": ("$$", "display"),
            r"\(": (r"\)", "inline"),
            r"\[": (r"\]", "display"),
        }
        if value in opening:
            stack.append(opening[value])


def scan(text: str) -> tuple[Token, ...]:
    """Tokenize unchanged source while tracking inline and displayed math."""
    tokens = []
    stack: list[tuple[str, MathContext]] = []
    offset = 0
    while offset < len(text):
        token = _read_token(text, offset)
        tokens.append(replace(token, math=stack[-1][1] if stack else "text"))
        if token.kind in {"environment", "delimiter", "command"}:
            _math_transition(token, stack)
        offset = token.end
    return tuple(tokens)
