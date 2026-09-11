import re
from collections.abc import Iterable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from latex_linting.document import Document
from latex_linting.rules.model import Rule
from latex_linting.source import Finding, Source

_ENTRY_START = re.compile(r"@\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*([{(])")
_SKIP_TYPES = frozenset({"comment", "string", "preamble"})


def _skip_ws_and_comments(text: str, idx: int) -> int:
    """Advance index past whitespace and percent comments."""
    while idx < len(text):
        if text[idx].isspace():
            idx += 1
        elif text[idx] == "%":
            eol = text.find("\n", idx)
            if eol == -1:
                return len(text)
            idx = eol + 1
        else:
            break
    return idx


def _read_braced_value(text: str, idx: int) -> tuple[str, int]:
    """Read a brace-delimited field value, respecting escaped braces and nesting."""
    depth = 1
    v_start = idx + 1
    idx += 1
    while idx < len(text) and depth > 0:
        c = text[idx]
        if c == "\\":
            idx += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                break
        idx += 1
    val = text[v_start:idx]
    return val, idx + 1 if idx < len(text) else idx


def _read_quoted_value(text: str, idx: int) -> tuple[str, int]:
    """Read a quote-delimited field value, respecting escaped characters and braces."""
    v_start = idx + 1
    idx += 1
    depth = 0
    while idx < len(text):
        c = text[idx]
        if c == "\\":
            idx += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            if depth > 0:
                depth -= 1
        elif c == '"' and depth == 0:
            break
        idx += 1
    val = text[v_start:idx]
    return val, idx + 1 if idx < len(text) else idx


def _read_field_value(text: str, start: int) -> tuple[str, int]:
    """Read a braced, quoted, or bare field value, including string concatenation with #."""
    chunks: list[str] = []
    idx = _skip_ws_and_comments(text, start)
    while idx < len(text):
        char = text[idx]
        if char == "{":
            val, idx = _read_braced_value(text, idx)
            chunks.append(val)
        elif char == '"':
            val, idx = _read_quoted_value(text, idx)
            chunks.append(val)
        else:
            match = re.match(r"[^,#\s{}()]+", text[idx:])
            if not match:
                break
            chunks.append(match.group(0))
            idx += match.end()
        idx = _skip_ws_and_comments(text, idx)
        if idx < len(text) and text[idx] == "#":
            idx = _skip_ws_and_comments(text, idx + 1)
            continue
        break
    return " ".join(chunks).strip(), idx


def _parse_entry_body(text: str, start: int, close_delim: str) -> tuple[str, dict[str, str], int]:
    """Parse citation key and field-value pairs up to the matching entry closing delimiter."""
    idx = _skip_ws_and_comments(text, start)
    if idx >= len(text) or text[idx] == close_delim:
        return "", {}, idx + (1 if idx < len(text) else 0)

    key_match = re.match(r"[^,\s{}()]+", text[idx:])
    key = key_match.group(0) if key_match else ""
    idx += len(key)
    idx = _skip_ws_and_comments(text, idx)
    if idx < len(text) and text[idx] == ",":
        idx += 1

    fields: dict[str, str] = {}
    while idx < len(text):
        idx = _skip_ws_and_comments(text, idx)
        if idx >= len(text) or text[idx] == close_delim:
            if idx < len(text):
                idx += 1
            break
        if text[idx] == ",":
            idx += 1
            continue

        field_match = re.match(r"([a-zA-Z_][a-zA-Z0-9_-]*)\s*=", text[idx:])
        if not field_match:
            idx += 1
            continue

        field_name = field_match.group(1).lower()
        val_start = idx + field_match.end()
        value, idx = _read_field_value(text, val_start)
        if value:
            fields[field_name] = value

    return key, fields, idx


def _skip_entry(text: str, start: int, close_delim: str) -> int:
    """Skip an ignored entry (comment/string/preamble) to its closing delimiter."""
    idx = start
    depth = 1
    while idx < len(text) and depth > 0:
        c = text[idx]
        if c == "\\":
            idx += 2
            continue
        if c in "({":
            depth += 1
        elif c in ")}":
            depth -= 1
            if depth == 0 or c == close_delim:
                idx += 1
                break
        idx += 1
    return idx


def _missing_creator(entry_type: str, fields: dict[str, str]) -> str | None:
    """Identify missing creator field depending on entry type."""
    if entry_type == "manual":
        if not any(f in fields for f in ("author", "editor", "organization")):
            return "author (or editor or organization)"
    elif entry_type in {"techreport", "report", "standard"}:
        if not any(f in fields for f in ("author", "editor", "institution")):
            return "author (or editor or institution)"
    elif entry_type in {"thesis", "phdthesis", "mastersthesis"}:
        if "author" not in fields:
            return "author"
    elif not any(f in fields for f in ("author", "editor")):
        return "author (or editor)"
    return None


def _missing_year(entry_type: str, fields: dict[str, str]) -> str | None:
    """Identify missing publication year or date depending on entry type."""
    if entry_type in {"misc", "online", "electronic", "www"}:
        if not any(f in fields for f in ("year", "date", "urldate")):
            return "year (or date or urldate)"
    elif not any(f in fields for f in ("year", "date")):
        return "year (or date)"
    return None


def _missing_article_fields(fields: dict[str, str]) -> list[str]:
    """Identify missing fields specific to journal articles."""
    missing: list[str] = []
    if not any(f in fields for f in ("journal", "journaltitle")):
        missing.append("journal (or journaltitle)")
    if "volume" not in fields:
        missing.append("volume")
    if "pages" not in fields:
        missing.append("pages")
    if "doi" not in fields:
        missing.append("doi")
    return missing


def _missing_inproceedings_fields(fields: dict[str, str]) -> list[str]:
    """Identify missing fields specific to conference proceedings."""
    missing: list[str] = []
    if "booktitle" not in fields:
        missing.append("booktitle")
    if "pages" not in fields:
        missing.append("pages")
    if not any(f in fields for f in ("doi", "isbn")):
        missing.append("doi or isbn")
    return missing


def _missing_book_fields(entry_type: str, fields: dict[str, str]) -> list[str]:
    """Identify missing fields specific to books and collections."""
    missing: list[str] = []
    if entry_type == "book":
        if "publisher" not in fields:
            missing.append("publisher")
        if not any(f in fields for f in ("doi", "isbn")):
            missing.append("doi or isbn")
    else:
        if "booktitle" not in fields and (entry_type != "inbook" or "title" not in fields):
            missing.append("booktitle")
        if "publisher" not in fields:
            missing.append("publisher")
        if "pages" not in fields:
            missing.append("pages")
        if not any(f in fields for f in ("doi", "isbn")):
            missing.append("doi or isbn")
    return missing


def _missing_misc_fields(entry_type: str, fields: dict[str, str]) -> list[str]:
    """Identify missing fields specific to misc, reports, and theses."""
    missing: list[str] = []
    if entry_type in {"techreport", "report", "standard"}:
        if not any(f in fields for f in ("institution", "publisher")):
            missing.append("institution")
    elif entry_type in {"thesis", "phdthesis", "mastersthesis"}:
        if not any(f in fields for f in ("school", "institution")):
            missing.append("school (or institution)")
    elif entry_type in {"misc", "online", "electronic", "www", "software", "dataset"}:
        if not any(f in fields for f in ("howpublished", "url")):
            missing.append("howpublished or url")
    elif entry_type != "manual":
        venues = ("journal", "journaltitle", "booktitle", "publisher", "institution", "school", "howpublished")
        if not any(f in fields for f in venues):
            missing.append("publication venue")
    return missing


def _missing_fields_for_entry(entry_type: str, fields: dict[str, str]) -> list[str]:
    """Determine list of missing mandatory BibLaTeX fields based on entry type."""
    missing: list[str] = []

    creator = _missing_creator(entry_type, fields)
    if creator:
        missing.append(creator)

    if "title" not in fields:
        missing.append("title")

    year = _missing_year(entry_type, fields)
    if year:
        missing.append(year)

    if entry_type == "article":
        missing.extend(_missing_article_fields(fields))
    elif entry_type in {"book", "incollection", "inbook"}:
        missing.extend(_missing_book_fields(entry_type, fields))
    elif entry_type in {"inproceedings", "conference"}:
        missing.extend(_missing_inproceedings_fields(fields))
    else:
        missing.extend(_missing_misc_fields(entry_type, fields))

    return missing


def _evaluate_bib_source(source: Source) -> Iterable[Finding]:
    """Scan a bibliography source for entries missing mandatory BibLaTeX fields."""
    text = source.text
    offset = 0
    while offset < len(text):
        match = _ENTRY_START.search(text, offset)
        if match is None:
            break

        entry_start = match.start()
        entry_type = match.group(1).lower()
        open_delim = match.group(2)
        close_delim = "}" if open_delim == "{" else ")"

        if entry_type in _SKIP_TYPES:
            offset = _skip_entry(text, match.end(), close_delim)
            continue

        key, fields, next_offset = _parse_entry_body(text, match.end(), close_delim)
        missing = _missing_fields_for_entry(entry_type, fields)
        if missing:
            explanation = (
                f"Bibliography entry '{key}' (@{entry_type}) is missing required field(s): {', '.join(missing)}."
            )
            correction = f"Add {', '.join(missing)} to entry '{key}'."
            yield source.finding(entry_start, RULE.rule_id, explanation, correction)

        offset = max(next_offset, match.end())


def _evaluate(document: "Document") -> Iterable[Finding]:
    """Evaluate all bibliography entries across loaded .bib files and inline sources."""
    for bib_node in document.bib_nodes:
        yield from _evaluate_bib_source(bib_node.source)
    for source in document.sources:
        if _ENTRY_START.search(source.text):
            yield from _evaluate_bib_source(source)


RULE = Rule(
    rule_id="CITE-08",
    explanation=(
        "Bibliography entries in .bib must contain complete metadata "
        "(author, title, venue, year, and type-specific fields like volume, pages, DOI, or ISBN)."
    ),
    correction="Add the missing mandatory fields to the bibliography entry in the .bib file.",
    passing_examples=(
        (
            "@article{smith2020,\n"
            "  author = {Smith, John and Doe, Jane},\n"
            "  title = {Advances in Control Theory},\n"
            "  journal = {IEEE Transactions on Automatic Control},\n"
            "  year = {2020},\n"
            "  volume = {65},\n"
            "  pages = {100--115},\n"
            "  doi = {10.1109/TAC.2020.1234567},\n"
            "}"
        ),
        (
            "@book{adamy2007,\n"
            "  author = {Adamy, Juergen},\n"
            "  title = {Systemdynamik und Regelungstechnik II},\n"
            "  publisher = {Shaker},\n"
            "  year = {2007},\n"
            "  isbn = {978-3-8322-6800-8},\n"
            "}"
        ),
    ),
    failing_examples=(
        (
            "@article{smith2020,\n"
            "  author = {Smith, John},\n"
            "  title = {Advances in Control Theory},\n"
            "  journal = {IEEE Transactions on Automatic Control},\n"
            "  year = {2020},\n"
            "}"
        ),
        (
            "@book{adamy2007,\n"
            "  author = {Adamy, Juergen},\n"
            "  title = {Systemdynamik und Regelungstechnik II},\n"
            "  publisher = {Shaker},\n"
            "  year = {2007},\n"
            "}"
        ),
    ),
    limits=(
        "Validates completeness of required BibLaTeX metadata fields per entry type in .bib files. "
        "Checks author/editor, title, and year/date for all entries; journal, volume, pages, and doi for @article; "
        "publisher and doi/isbn for @book; booktitle, pages, and doi/isbn for @inproceedings. "
        "Does not query remote DOI/ISBN databases or verify the factual accuracy of citations. "
        "Entries lacking assigned DOI/ISBN can be suppressed with '% latex-lint: ignore=CITE-08'."
    ),
    evaluate=_evaluate,
)
