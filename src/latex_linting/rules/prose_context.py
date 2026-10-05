from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.scanner import Token
from latex_linting.source import Source

_NON_PROSE_ENVIRONMENTS = frozenset(
    {
        "tikzpicture",
        "pgfpicture",
        "pgfplots",
        "axis",
        "circuitikz",
        "quantikz",
        "tikzcd",
        "forest",
        "picture",
        "asy",
        "filecontents",
        "filecontents*",
    }
)

_ACRO_COMMANDS = frozenset(
    {
        r"\ac",
        r"\Ac",
        r"\acs",
        r"\Acs",
        r"\acl",
        r"\Acl",
        r"\acf",
        r"\Acf",
        r"\acp",
        r"\Acp",
        r"\acsp",
        r"\Acsp",
        r"\aclp",
        r"\Aclp",
        r"\acfp",
        r"\Acfp",
        r"\iac",
        r"\Iac",
        r"\acuse",
        r"\acreset",
        r"\acsetup",
        r"\DeclareAcronym",
    }
)

_DOUBLE_ARG_COMMANDS = frozenset(
    {
        r"\DeclareAcronym",
        r"\setlength",
        r"\setcounter",
        r"\addtocounter",
    }
)

_SYNTAX_COMMANDS = (
    frozenset(
        {
            r"\addbibresource",
            r"\addtocounter",
            r"\autoref",
            r"\autocite",
            r"\bibliography",
            r"\bibliographystyle",
            r"\cite",
            r"\citeauthor",
            r"\citep",
            r"\citet",
            r"\citeyear",
            r"\cref",
            r"\Cref",
            r"\documentclass",
            r"\eqref",
            r"\footcite",
            r"\fullcite",
            r"\include",
            r"\includegraphics",
            r"\includeonly",
            r"\input",
            r"\label",
            r"\nocite",
            r"\pageref",
            r"\pagenumbering",
            r"\pagestyle",
            r"\parencite",
            r"\ref",
            r"\RequirePackage",
            r"\setcounter",
            r"\setlength",
            r"\subfile",
            r"\textcite",
            r"\thispagestyle",
            r"\url",
            r"\usepackage",
        }
    )
    | _ACRO_COMMANDS
)


@dataclass
class _SyntaxTracker:
    """Track command argument brace depth and environment nesting across document tokens."""

    depth: int = 0
    expecting_braces: int = 0
    env_stack: list[str] = field(default_factory=list)

    def handle_environment(self, value: str) -> None:
        """Track entry and exit of LaTeX environments."""
        name = value[value.index("{") + 1 : -1]
        if value.startswith(r"\begin"):
            self.env_stack.append(name)
        elif value.startswith(r"\end"):
            while self.env_stack and self.env_stack[-1] != name:
                self.env_stack.pop()
            if self.env_stack:
                self.env_stack.pop()

    @property
    def in_non_prose_env(self) -> bool:
        """Return True if currently inside a non-prose graphic or diagram environment."""
        return any(env in _NON_PROSE_ENVIRONMENTS for env in self.env_stack)

    def handle_command(self, value: str) -> None:
        """Update expected brace count for recognized syntax commands."""
        if value in _DOUBLE_ARG_COMMANDS:
            self.expecting_braces = 2
        elif value in _SYNTAX_COMMANDS:
            self.expecting_braces = 1
        else:
            self.expecting_braces = 0

    def handle_brace(self, value: str) -> None:
        """Update syntax depth when encountering opening or closing braces."""
        if value == "{":
            if self.expecting_braces > 0 and self.depth == 0:
                self.depth = 1
                self.expecting_braces -= 1
            elif self.depth > 0:
                self.depth += 1
        elif value == "}" and self.depth > 0:
            self.depth -= 1

    def handle_text(self, value: str) -> bool:
        """Update expected braces on non-brace text, returning True if token is prose."""
        if self.depth == 0 and self.expecting_braces > 0:
            stripped = value.strip()
            if stripped and stripped != "*":
                self.expecting_braces = 0
        return self.depth == 0 and self.expecting_braces == 0 and not self.in_non_prose_env


def iter_prose_tokens(document: "Document") -> Iterable[tuple[Source, Token]]:
    """Yield text tokens that occur outside math, comments, literals, and command syntax."""
    tracker = _SyntaxTracker()

    for source, token in document.traverse():
        if token.kind == "environment":
            tracker.handle_environment(token.value)
        elif token.kind == "command":
            tracker.handle_command(token.value)
        elif token.kind == "brace":
            tracker.handle_brace(token.value)
        elif token.kind == "text" and token.math == "text" and tracker.handle_text(token.value):
            yield source, token
