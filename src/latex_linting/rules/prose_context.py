from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.scanner import Token
from latex_linting.source import Source

_SYNTAX_COMMANDS = frozenset(
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


def iter_prose_tokens(document: "Document") -> Iterable[tuple[Source, Token]]:
    """Yield text tokens that occur outside math, comments, literals, and command syntax."""
    syntax_depth = 0
    expecting_syntax_brace = False

    for source, token in document.traverse():
        if token.kind == "command":
            if token.value in _SYNTAX_COMMANDS:
                expecting_syntax_brace = True
            continue

        if token.kind == "brace":
            if token.value == "{":
                if expecting_syntax_brace:
                    syntax_depth += 1
                    expecting_syntax_brace = False
                elif syntax_depth > 0:
                    syntax_depth += 1
            elif token.value == "}" and syntax_depth > 0:
                syntax_depth -= 1
            continue

        if token.kind == "text" and token.math == "text" and syntax_depth == 0:
            yield source, token
