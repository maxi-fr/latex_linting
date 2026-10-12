import re
import sys
from collections.abc import Sequence
from pathlib import Path

from latex_linting.rules.typo_01 import _TYPO_01_COMMANDS, _inspect_preceding
from latex_linting.rules.typo_02 import (
    _CATEGORY_NOUN_PATTERN,
    _NUMBER_UNIT_PATTERN,
    _TIME_PATTERN,
    _TITLE_PATTERN,
)
from latex_linting.rules.typo_03 import _ABBREVIATION_PATTERN
from latex_linting.rules.typo_04 import _PARAMETERLESS_COMMANDS, _is_swallowed_space
from latex_linting.rules.typo_05 import _ISO_DATE_PATTERN, _RANGE_PATTERN
from latex_linting.scanner import Token, scan

_ABBREVIATIONS = frozenset(
    {
        # English academic & general
        "alg.",
        "al.",
        "approx.",
        "assoc.",
        "ca.",
        "cf.",
        "c.f.",
        "ch.",
        "chs.",
        "col.",
        "cor.",
        "def.",
        "dept.",
        "dr.",
        "ed.",
        "eds.",
        "e.g.",
        "eq.",
        "eqs.",
        "et al.",
        "et seq.",
        "etc.",
        "fig.",
        "figs.",
        "gl.",
        "gls.",
        "hr.",
        "hrs.",
        "i.a.",
        "ibid.",
        "i.e.",
        "inc.",
        "jr.",
        "lem.",
        "ltd.",
        "max.",
        "min.",
        "mr.",
        "mrs.",
        "ms.",
        "no.",
        "nos.",
        "p.",
        "pp.",
        "prof.",
        "prop.",
        "ref.",
        "refs.",
        "rep.",
        "rev.",
        "sec.",
        "secs.",
        "sr.",
        "std.",
        "tab.",
        "tabs.",
        "thm.",
        "univ.",
        "viz.",
        "vol.",
        "vols.",
        "vs.",
        # German academic & general
        "abb.",
        "abs.",
        "art.",
        "bd.",
        "bspw.",
        "bzw.",
        "d.h.",
        "evtl.",
        "ff.",
        "gem.",
        "ggf.",
        "hrsg.",
        "inkl.",
        "nr.",
        "s.",
        "u.a.",
        "u.ä.",
        "usw.",
        "u.v.m.",
        "u.z.",
        "vgl.",
        "z.b.",
        "z.t.",
    }
)

_PROTECTED_ENVIRONMENTS = frozenset(
    {
        "tabular",
        "tabular*",
        "tabularx",
        "tabulary",
        "longtable",
        "tikzpicture",
        "picture",
        "pgfplots",
    }
)

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
        r"\DeclareMathOperator",
        r"\def",
        r"\documentclass",
        r"\eqref",
        r"\footcite",
        r"\fullcite",
        r"\href",
        r"\include",
        r"\includegraphics",
        r"\includeonly",
        r"\input",
        r"\label",
        r"\newcommand",
        r"\nocite",
        r"\pageref",
        r"\pagenumbering",
        r"\pagestyle",
        r"\parencite",
        r"\ref",
        r"\renewcommand",
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

_HEADING_COMMANDS = frozenset(
    {
        r"\author",
        r"\caption",
        r"\chapter",
        r"\date",
        r"\paragraph",
        r"\part",
        r"\section",
        r"\subparagraph",
        r"\subsection",
        r"\subsubsection",
        r"\title",
    }
)

_ATTACHED_COMMAND_NAMES = frozenset(
    {
        r"\autocite",
        r"\cite",
        r"\citeauthor",
        r"\citep",
        r"\citet",
        r"\citeyear",
        r"\footcite",
        r"\fullcite",
        r"\index",
        r"\label",
        r"\parencite",
        r"\textcite",
    }
)

_STRUCTURAL_COMMANDS = _HEADING_COMMANDS | frozenset(
    {
        r"\addbibresource",
        r"\addtocounter",
        r"\appendix",
        r"\backmatter",
        r"\bibliography",
        r"\bibliographystyle",
        r"\centering",
        r"\cleardoublepage",
        r"\clearpage",
        r"\DeclareMathOperator",
        r"\def",
        r"\documentclass",
        r"\frontmatter",
        r"\include",
        r"\includegraphics",
        r"\includeonly",
        r"\input",
        r"\label",
        r"\listoffigures",
        r"\listoftables",
        r"\mainmatter",
        r"\maketitle",
        r"\newcommand",
        r"\newpage",
        r"\noindent",
        r"\pagebreak",
        r"\pagenumbering",
        r"\pagestyle",
        r"\raggedleft",
        r"\raggedright",
        r"\renewcommand",
        r"\RequirePackage",
        r"\setcounter",
        r"\setlength",
        r"\subfile",
        r"\tableofcontents",
        r"\thispagestyle",
        r"\usepackage",
    }
)

_HARD_BREAK_RE = re.compile(r"(?:\\\\(?:\[[^\]]*\])?|\\newline|\\linebreak)$")

_PREFIX_SNIPPET_LENGTH = 25
_MIN_INITIAL_INDEX = 2
_MIN_DOUBLE_QUOTES = 2

_SENTENCE_STARTER_QUOTES = frozenset({'"', "'", "\u201c", "\u2018", "\u00bb", "\u00ab"})
_SENTENCE_STARTER_BRACKETS = frozenset({"(", "[", "{"})

_SINGLE_QUOTE_RE = re.compile(
    r"(?<![a-zA-Z0-9\\])(?:(?<=^)|(?<=[\s(\[{<:;~]))'([a-zA-Z0-9][^'\r\n]*?[a-zA-Z0-9.,!?:;])'(?=[ \t\r\n.,!?:;)\]}>]|$)"
)
_MULTI_SPACE_RE = re.compile(r"(?<=\S)[ \t]{2,}")


def _is_escaped(text: str, idx: int) -> bool:
    """Return True if character at idx is preceded by an odd number of backslashes."""
    backslashes = 0
    k = idx - 1
    while k >= 0 and text[k] == "\\":
        backslashes += 1
        k -= 1
    return backslashes % 2 == 1


def _has_unescaped_comment(line: str) -> bool:
    """Return True if line contains an unescaped comment character."""
    return any(char == "%" and not _is_escaped(line, idx) for idx, char in enumerate(line))


def _starts_with_structural_command(line: str) -> bool:
    """Return True if line starts with a structural LaTeX command."""
    match = re.match(r"^\\([a-zA-Z*]+)", line)
    if not match:
        return False
    cmd = "\\" + match.group(1).rstrip("*")
    return cmd in _STRUCTURAL_COMMANDS


def _consume_balanced(text: str, start: int, open_char: str, close_char: str) -> int:
    """Consume balanced brackets or braces starting at start offset."""
    if start >= len(text) or text[start] != open_char:
        return start
    depth = 0
    idx = start
    while idx < len(text):
        if text[idx] == open_char and not _is_escaped(text, idx):
            depth += 1
        elif text[idx] == close_char and not _is_escaped(text, idx):
            depth -= 1
            if depth == 0:
                return idx + 1
        idx += 1
    return idx


def _consume_command_arguments(text: str, start: int) -> int:
    """Consume optional bracket and mandatory brace arguments following a command."""
    idx = start
    while idx < len(text):
        scan_idx = idx
        while scan_idx < len(text) and text[scan_idx] in " \t":
            scan_idx += 1
        if scan_idx < len(text) and text[scan_idx] == "[":
            idx = _consume_balanced(text, scan_idx, "[", "]")
        elif scan_idx < len(text) and text[scan_idx] == "{":
            idx = _consume_balanced(text, scan_idx, "{", "}")
        else:
            break
    return idx


def _mask_environment(text: str, tokens: Sequence[Token], idx: int, mask: bytearray) -> int:
    """Mask tokens inside a protected environment and return the advanced token index."""
    token = tokens[idx]
    value = token.value
    token_count = len(tokens)
    if value.startswith(r"\begin"):
        name = value[value.index("{") + 1 : -1]
        if name in _PROTECTED_ENVIRONMENTS:
            closing_pattern = re.compile(r"\\end\s*\{" + re.escape(name) + r"\}")
            search_match = closing_pattern.search(text, token.end)
            env_end = search_match.end() if search_match else len(text)
            mask[token.start : env_end] = b"\x01" * (env_end - token.start)
            while idx < token_count and tokens[idx].end <= env_end:
                idx += 1
            return idx
    return idx + 1


def _mask_command(text: str, tokens: Sequence[Token], idx: int, mask: bytearray) -> int:
    """Mask syntax command arguments and return the advanced token index."""
    token = tokens[idx]
    token_count = len(tokens)
    if token.value in _SYNTAX_COMMANDS or token.value in _HEADING_COMMANDS:
        arg_end = _consume_command_arguments(text, token.end)
        mask[token.start : arg_end] = b"\x01" * (arg_end - token.start)
        while idx < token_count and tokens[idx].end <= arg_end:
            idx += 1
        return idx
    return idx + 1


def _build_protected_mask(text: str) -> bytearray:
    """Return a bytearray mask with non-zero bytes for protected character ranges."""
    mask = bytearray(len(text))
    tokens = scan(text)
    token_count = len(tokens)
    idx = 0

    while idx < token_count:
        token = tokens[idx]

        if token.kind in {"comment", "literal", "delimiter"} or token.math in {"inline", "display"}:
            mask[token.start : token.end] = b"\x01" * (token.end - token.start)
            idx += 1
            continue

        if token.kind == "environment":
            idx = _mask_environment(text, tokens, idx, mask)
            continue

        if token.kind == "command":
            idx = _mask_command(text, tokens, idx, mask)
            continue

        idx += 1

    return mask


_INITIAL_PREFIX_RE = re.compile(
    r"\b(?:[A-Z]\.|Dr\.|Prof\.|Mr\.|Mrs\.|Ms\.|by|in|at|on|of|to|for|from|after|before|with|and|or|as|see|between|about|von|de|van|den|der|das|ein|eine)\s+[A-Z]\.$",
    re.IGNORECASE,
)


def _is_initial(text: str, period_idx: int) -> bool:
    """Return True if period_idx forms part of a person's name initial."""
    if period_idx <= 0 or not text[period_idx - 1].isupper():
        return False

    char_before = text[period_idx - _MIN_INITIAL_INDEX] if period_idx >= _MIN_INITIAL_INDEX else " "
    if char_before not in " \t(~\"'":
        return False

    line_start = text.rfind("\n", 0, period_idx)
    line_start = 0 if line_start == -1 else line_start + 1
    if re.match(r"^[ \t]*[A-Z]\.$", text[line_start : period_idx + 1]):
        return True

    snippet = text[max(0, period_idx - _PREFIX_SNIPPET_LENGTH) : period_idx + 1]
    if _INITIAL_PREFIX_RE.search(snippet):
        return True

    return bool(re.match(r"^\s+[A-Z]\.", text[period_idx + 1 :]))


def _is_multipart_abbreviation(text: str, period_idx: int) -> bool:
    """Return True if period_idx is the first dot in a multi-part abbreviation."""
    if period_idx <= 0 or not text[period_idx - 1].isalpha():
        return False
    char_before = text[period_idx - 1]
    next_part = re.match(r"^(\s+|\\\,|~)([a-zA-Z])\.", text[period_idx + 1 :])
    if not next_part:
        return False
    pair = f"{char_before.lower()}.{next_part.group(2).lower()}."
    if pair in {"z.b.", "d.h.", "u.a.", "u.ä.", "e.g.", "i.e.", "z.t.", "c.f."}:
        return True
    return char_before.isupper() and next_part.group(2).isupper()


def _is_abbreviation(text: str, period_idx: int) -> bool:
    """Return True if period at period_idx is part of an abbreviation or initial."""
    snippet = text[max(0, period_idx - _PREFIX_SNIPPET_LENGTH) : period_idx + 1]

    condensed = re.sub(r"(\\?\,|~|\s+)", "", snippet).lower()
    if condensed.endswith(("e.g.", "i.e.", "z.b.", "d.h.", "u.a.", "u.ä.", "z.t.", "c.f.")):
        return True

    if _is_multipart_abbreviation(text, period_idx):
        return True

    normalized = re.sub(r"(\\?\,|~|\s+)", " ", snippet).lower()
    for abbr in _ABBREVIATIONS:
        if re.search(rf"(?:^|[\s(~'\"`]){re.escape(abbr)}$", normalized):
            return True

    if re.search(r"\b[A-Z]\.[A-Z]\.$", snippet):
        return True

    return _is_initial(text, period_idx)


def _advance_past_trailers(text: str, start: int) -> int:
    """Advance past closing quotes, brackets, braces, and attached citations or labels."""
    idx = start
    while idx < len(text):
        if text[idx] in "')]\u201d\u2019}\"":
            idx += 1
            continue
        if text[idx : idx + 2] == "''":
            idx += 2
            continue
        if text[idx] == "~" and idx + 1 < len(text) and text[idx + 1] == "\\":
            idx += 1
        if text[idx] == "\\":
            cmd_match = re.match(r"^\\[a-zA-Z*]+", text[idx:])
            if cmd_match and cmd_match.group(0) in _ATTACHED_COMMAND_NAMES:
                idx = _consume_command_arguments(text, idx + len(cmd_match.group(0)))
                continue
        break
    return idx


def _is_terminal_period(text: str, pos: int) -> bool:
    """Return True if period at pos is valid sentence terminal punctuation."""
    text_len = len(text)
    if (pos > 0 and text[pos - 1] == ".") or (pos + 1 < text_len and text[pos + 1] == "."):
        return False
    if pos > 0 and text[pos - 1].isdigit() and pos + 1 < text_len and text[pos + 1].isdigit():
        return False
    line_start = text.rfind("\n", 0, pos)
    line_start = 0 if line_start == -1 else line_start + 1
    if re.match(r"^[ \t]*(?:\d+(?:\.\d+)*|[a-zA-Z]|\([a-zA-Z0-9]+\))\.$", text[line_start : pos + 1]):
        return False
    return not _is_abbreviation(text, pos)


def _is_sentence_starter(text: str, idx: int) -> bool:
    """Return True if character at idx can begin a new sentence."""
    if idx >= len(text):
        return False
    char = text[idx]
    if char.isupper() or char in {"\\", "$"}:
        return True
    if char in _SENTENCE_STARTER_QUOTES or char in _SENTENCE_STARTER_BRACKETS:
        return True
    return text[idx : idx + 2] == "``"


def _find_line_comment_match(text: str, pos: int) -> tuple[str, int, int] | None:
    """Find trailing cite-checked comment on current line and return its text and span."""
    line_end = text.find("\n", pos)
    if line_end == -1:
        line_end = len(text)
    match = re.search(r"([ \t]*%\s*cite-checked\s*:[^\r\n]*)$", text[pos:line_end])
    if not match:
        return None
    start = pos + match.start()
    end = pos + match.end()
    return match.group(1), start, end


def _compute_citation_comment_replacements(
    text: str,
    pos: int,
    after_trailers: int,
    next_non_space: int,
    newline_indent: str,
) -> tuple[tuple[int, int, str], tuple[int, int, str] | None]:
    """Return replacement tuples associating trailing cite-checked comment with the sentence."""
    comment_info = _find_line_comment_match(text, pos)
    if not comment_info:
        return (after_trailers, next_non_space, newline_indent), None

    comment_str, c_start, c_end = comment_info
    line_start = text.rfind("\n", 0, pos)
    line_start = 0 if line_start == -1 else line_start + 1
    sent_text = text[line_start:after_trailers]
    rest_text = text[next_non_space:c_start]

    has_cite_in_sent = bool(re.search(r"\\(?:cite|autocite|parencite|textcite|citep|citet|footcite)\b", sent_text))
    has_cite_in_rest = bool(re.search(r"\\(?:cite|autocite|parencite|textcite|citep|citet|footcite)\b", rest_text))

    if has_cite_in_sent and not has_cite_in_rest:
        repl = (after_trailers, next_non_space, f"{comment_str.rstrip()}{newline_indent}")
        return repl, (c_start, c_end, "")
    if has_cite_in_sent and has_cite_in_rest:
        repl = (after_trailers, next_non_space, f"{comment_str.rstrip()}{newline_indent}")
        return repl, None

    return (after_trailers, next_non_space, newline_indent), None


def _find_sentence_replacement(
    text: str,
    pos: int,
    punct_end: int,
    newline: str,
) -> tuple[tuple[int, int, str], tuple[int, int, str] | None] | None:
    """Return whitespace range and newline replacement if a sentence break is detected."""
    text_len = len(text)
    after_trailers = _advance_past_trailers(text, punct_end)

    if after_trailers >= text_len or text[after_trailers] not in " \t":
        return None

    next_non_space = after_trailers
    while next_non_space < text_len and text[next_non_space] in " \t":
        next_non_space += 1

    if not _is_sentence_starter(text, next_non_space):
        return None

    line_start = text.rfind("\n", 0, pos)
    line_start = 0 if line_start == -1 else line_start + 1
    line_prefix = text[line_start:pos]
    indent_match = re.match(r"^[ \t]*", line_prefix)
    indent = indent_match.group(0) if indent_match else ""

    return _compute_citation_comment_replacements(
        text,
        pos,
        after_trailers,
        next_non_space,
        newline + indent,
    )


def _format_command_syntax(text: str) -> str:
    """Insert nonbreaking spaces before references and empty braces after parameterless commands."""
    tokens = scan(text)
    replacements: list[tuple[int, int, str]] = []

    for token in tokens:
        if token.kind == "command" and token.math == "text":
            if token.value in _TYPO_01_COMMANDS and _inspect_preceding(text, token.start):
                prefix = text[: token.start]
                line_start = prefix.rfind("\n") + 1
                line_before = prefix[line_start : token.start]
                if not line_before.strip():
                    prev_end = line_start - 1
                    while prev_end > 0 and text[prev_end - 1] in " \t":
                        prev_end -= 1
                    replacements.append((prev_end, token.start, "~"))
                else:
                    spaces_len = len(line_before) - len(line_before.rstrip(" \t"))
                    replacements.append((token.start - spaces_len, token.start, "~"))
            elif token.value in _PARAMETERLESS_COMMANDS and _is_swallowed_space(text, token.end):
                replacements.append((token.end, token.end, "{}"))

    if not replacements:
        return text

    replacements.sort(key=lambda r: r[0])
    chunks: list[str] = []
    last_idx = 0
    for start_idx, end_idx, repl in replacements:
        chunks.append(text[last_idx:start_idx])
        chunks.append(repl)
        last_idx = end_idx
    chunks.append(text[last_idx:])
    return "".join(chunks)


def _replace_double_quotes_in_line(line: str) -> str:
    """Convert unescaped straight double quotes on one line into LaTeX quotes."""
    indices = [i for i, ch in enumerate(line) if ch == '"' and not _is_escaped(line, i)]
    if len(indices) < _MIN_DOUBLE_QUOTES:
        return line
    chars = list(line)
    pair_count = len(indices) // 2
    for p in range(pair_count - 1, -1, -1):
        open_idx = indices[p * 2]
        close_idx = indices[p * 2 + 1]
        chars[close_idx] = "''"
        chars[open_idx] = "``"
    return "".join(chars)


def _sub_abbreviation(match: re.Match[str]) -> str:
    """Format abbreviation with a thin space."""
    val = match.group(1)
    return f"{val[0]}.\\,{val[-2]}."


def _sub_numeric_range(match: re.Match[str], date_spans: Sequence[tuple[int, int]]) -> str:
    """Replace single-hyphen numeric range with en-dash when not an ISO date."""
    if any(start <= match.start(2) < end for start, end in date_spans):
        return match.group(0)
    return f"{match.group(1)}--{match.group(3)}"


def _format_prose_segment(segment: str) -> str:
    """Format an unmasked prose segment for typography and whitespace."""
    segment = _ABBREVIATION_PATTERN.sub(_sub_abbreviation, segment)
    segment = _CATEGORY_NOUN_PATTERN.sub(r"\1~\2", segment)
    segment = _TITLE_PATTERN.sub(r"\1~\2", segment)
    segment = _TIME_PATTERN.sub(lambda m: f"{m.group(1)}~{m.group(2) or 'Uhr'}", segment)
    segment = _NUMBER_UNIT_PATTERN.sub(r"\1~\2", segment)

    dates = [m.span() for m in _ISO_DATE_PATTERN.finditer(segment)]
    segment = _RANGE_PATTERN.sub(lambda m: _sub_numeric_range(m, dates), segment)

    lines = segment.split("\n")
    segment = "\n".join(_replace_double_quotes_in_line(line) for line in lines)

    segment = _SINGLE_QUOTE_RE.sub(r"`\1'", segment)

    return _MULTI_SPACE_RE.sub(" ", segment)


def _format_prose_typography(text: str) -> str:
    """Apply typography rules to unmasked prose segments."""
    mask = _build_protected_mask(text)
    chunks: list[str] = []
    idx = 0
    text_len = len(text)
    while idx < text_len:
        if mask[idx]:
            start = idx
            while idx < text_len and mask[idx]:
                idx += 1
            chunks.append(text[start:idx])
        else:
            start = idx
            while idx < text_len and not mask[idx]:
                idx += 1
            chunks.append(_format_prose_segment(text[start:idx]))
    return "".join(chunks)


def _line_ends_with_terminal_punct(
    text: str,
    line_start: int,
    line_content_end: int,
    mask: Sequence[int],
) -> bool:
    """Return True if line ends with valid sentence-terminal punctuation and trailers."""
    for pos in range(line_content_end - 1, line_start - 1, -1):
        if mask[pos]:
            continue
        char = text[pos]
        if char not in {".", "!", "?"}:
            continue

        if char in {"!", "?"}:
            punct_end = pos + 1
            while punct_end < line_content_end and text[punct_end] in {"!", "?"}:
                punct_end += 1
        elif _is_terminal_period(text, pos):
            punct_end = pos + 1
        else:
            continue

        after_trailers = _advance_past_trailers(text, punct_end)
        if after_trailers == line_content_end:
            return True

    return False


def _is_structural_boundary(before_stripped: str, after_stripped: str, trimmed_before: str) -> bool:
    """Return True if structural markers prevent combining lines across the boundary."""
    if re.search(r"\\(?:begin|end)\s*\{", before_stripped) or re.search(r"\\(?:begin|end)\s*\{", after_stripped):
        return True
    if re.match(r"^\\(?:item|bibitem|task)\b", after_stripped):
        return True
    if re.match(r"^[-*]\s+", after_stripped) or re.match(r"^\d+\.\s+", after_stripped):
        return True
    if trimmed_before.endswith((r"\[", r"\]", "$$")) or after_stripped.startswith((r"\[", r"\]", "$$")):
        return True
    return bool(_starts_with_structural_command(before_stripped) or _starts_with_structural_command(after_stripped))


def _should_combine_boundary(
    curr_line: tuple[int, int],
    line_after: str,
    text: str,
    mask: Sequence[int],
) -> bool:
    """Return True if line_before and line_after belong to the same sentence."""
    curr_line_start, nl_start_match = curr_line
    line_before = text[curr_line_start:nl_start_match]
    before_stripped = line_before.strip()
    after_stripped = line_after.strip()
    if not before_stripped or not after_stripped or mask[nl_start_match] != 0:
        return False

    if _has_unescaped_comment(line_before) or after_stripped.startswith("%"):
        return False

    trimmed_before = line_before.rstrip(" \t")
    if _HARD_BREAK_RE.search(trimmed_before):
        return False

    if _is_structural_boundary(before_stripped, after_stripped, trimmed_before):
        return False

    line_content_end = curr_line_start + len(trimmed_before)
    return not _line_ends_with_terminal_punct(text, curr_line_start, line_content_end, mask)


def _combine_sentence_lines(text: str) -> str:
    """Combine lines belonging to the same sentence into a single line."""
    mask = _build_protected_mask(text)
    newline_matches = list(re.finditer(r"\r?\n", text))
    if not newline_matches:
        return text

    replacements: list[tuple[int, int, str]] = []
    line_start = 0

    for i, match in enumerate(newline_matches):
        nl_start_match = match.start()
        nl_end_match = match.end()
        next_line_end = newline_matches[i + 1].start() if i + 1 < len(newline_matches) else len(text)

        curr_line_start = line_start
        line_before = text[curr_line_start:nl_start_match]
        line_after = text[nl_end_match:next_line_end]
        line_start = nl_end_match

        if not _should_combine_boundary((curr_line_start, nl_start_match), line_after, text, mask):
            continue

        trimmed_before = line_before.rstrip(" \t")
        nl_start = curr_line_start + len(trimmed_before)
        nl_end = nl_end_match
        while nl_end < next_line_end and text[nl_end] in " \t":
            nl_end += 1

        repl = "" if (trimmed_before.endswith("~") or (nl_end < len(text) and text[nl_end] == "~")) else " "
        replacements.append((nl_start, nl_end, repl))

    if not replacements:
        return text

    replacements.sort(key=lambda r: r[0])
    chunks: list[str] = []
    last_idx = 0
    for start_idx, end_idx, repl in replacements:
        chunks.append(text[last_idx:start_idx])
        chunks.append(repl)
        last_idx = end_idx
    chunks.append(text[last_idx:])
    return "".join(chunks)


def _split_sentences(text: str) -> str:
    """Format LaTeX source by placing a newline character after each sentence."""
    mask = _build_protected_mask(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    replacements: list[tuple[int, int, str]] = []

    pos = 0
    text_len = len(text)

    while pos < text_len:
        char = text[pos]

        if mask[pos] or char not in {".", "!", "?"}:
            pos += 1
            continue

        if char in {"!", "?"}:
            punct_end = pos + 1
            while punct_end < text_len and text[punct_end] in {"!", "?"}:
                punct_end += 1
        elif _is_terminal_period(text, pos):
            punct_end = pos + 1
        else:
            pos += 1
            continue

        replacement_pair = _find_sentence_replacement(text, pos, punct_end, newline)
        if replacement_pair is not None:
            primary_repl, cleanup_repl = replacement_pair
            replacements.append(primary_repl)
            if cleanup_repl is not None:
                replacements.append(cleanup_repl)
            pos = primary_repl[1]
            continue

        pos = punct_end

    if not replacements:
        return text

    replacements.sort(key=lambda r: r[0])
    chunks: list[str] = []
    last_idx = 0
    for start_idx, end_idx, repl in replacements:
        chunks.append(text[last_idx:start_idx])
        chunks.append(repl)
        last_idx = end_idx
    chunks.append(text[last_idx:])
    return "".join(chunks)


def format_latex(text: str) -> str:
    """Format LaTeX source by repairing typography, combining wrapped sentences, and placing one sentence per line."""
    text = _format_command_syntax(text)
    text = _combine_sentence_lines(text)
    text = _format_prose_typography(text)
    text = _split_sentences(text)
    return re.sub(r"[ \t]+(?=\r?\n|$)", "", text)


def _format_single_file(path: Path) -> int:
    """Read, format, and save an explicit LaTeX file."""
    try:
        content = path.read_text(encoding="utf-8")
        formatted = format_latex(content)
        if formatted != content:
            path.write_text(formatted, encoding="utf-8")
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"latex-lint: {path}: {error}\n")
        return 2
    return 0


def format_files(paths: Sequence[Path]) -> int:
    """Format explicit LaTeX files in-place with one sentence per line."""
    for path in paths:
        if not path.exists():
            sys.stderr.write(f"latex-lint: cannot find file '{path}'\n")
            return 2
        if not path.is_file():
            sys.stderr.write(f"latex-lint: '{path}' is not a regular file\n")
            return 2

    for path in paths:
        exit_code = _format_single_file(path)
        if exit_code != 0:
            return exit_code

    return 0
