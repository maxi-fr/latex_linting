import http
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx
import pypdf

from latex_linting.document import load_document
from latex_linting.scanner import Token, scan
from latex_linting.source import Source

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

_ENTRY_START = re.compile(r"@\s*([a-zA-Z_][a-zA-Z0-9_-]*)\s*([{(])")
_SKIP_TYPES = frozenset({"comment", "string", "preamble"})
_CITE_CHECKED_RE = re.compile(r"%\s*cite-checked\s*:\s*(.+?)\s*$")
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_UNPAYWALL_EMAIL = "unpaywall-cite-checker@users.noreply.github.com"
_MIN_SEARCH_TITLE_LEN = 5
_S2_MIN_REQUEST_INTERVAL = 1.0
_last_s2_request_time: float = 0.0


@dataclass(frozen=True)
class BibEntry:
    """Represent an entry in a BibTeX file."""

    key: str
    entry_type: str
    fields: dict[str, str]

    @property
    def title(self) -> str:
        """Return the cleaned title of the entry."""
        return self.fields.get("title", "")

    @property
    def author(self) -> str:
        """Return the author(s) of the entry."""
        return self.fields.get("author", "")

    @property
    def doi(self) -> str:
        """Return the normalized DOI without URL prefixes."""
        raw = self.fields.get("doi", "").strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
            if raw.lower().startswith(prefix):
                return raw[len(prefix) :].strip()
        return raw

    @property
    def eprint(self) -> str:
        """Return normalized arXiv / eprint identifier."""
        raw = self.fields.get("eprint", "").strip()
        if raw.lower().startswith("arxiv:"):
            return raw[6:].strip()
        return raw

    @property
    def url(self) -> str:
        """Return the URL field."""
        return self.fields.get("url", "").strip()

    @property
    def file(self) -> str:
        """Return the file field."""
        return self.fields.get("file", "").strip()


@dataclass(frozen=True)
class CitationOccurrence:
    """Represent an occurrence of a citation in a LaTeX document."""

    key: str
    filename: str
    line: int
    column: int
    command: str
    line_text: str
    status: str | None


@dataclass(frozen=True)
class UnretrievedRef:
    """Represent a reference that could not be automatically downloaded."""

    key: str
    title: str
    author: str
    doi: str
    url: str
    reason: str


@dataclass(frozen=True)
class FetchResult:
    """Hold results of an automatic reference fetching pass."""

    downloaded: tuple[tuple[str, Path], ...]
    unretrieved: tuple[UnretrievedRef, ...]
    existing: tuple[tuple[str, Path], ...]


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


def _skip_entry(text: str, start: int) -> int:
    """Skip an ignored entry (comment/string/preamble) to its closing delimiter."""
    idx = start
    depth = 1
    while idx < len(text) and depth > 0:
        c = text[idx]
        if c == "\\":
            idx += 2
            continue
        if c in ("{", "("):
            depth += 1
        elif c in ("}", ")"):
            depth -= 1
            if depth == 0:
                return idx + 1
        idx += 1
    return idx


def parse_bibtex(text: str) -> list[BibEntry]:
    """Parse BibTeX content into a list of BibEntry instances."""
    entries: list[BibEntry] = []
    idx = 0
    while idx < len(text):
        match = _ENTRY_START.search(text, idx)
        if not match:
            break
        entry_type = match.group(1).lower()
        open_delim = match.group(2)
        close_delim = "}" if open_delim == "{" else ")"
        body_start = match.end()

        if entry_type in _SKIP_TYPES:
            idx = _skip_entry(text, body_start)
            continue

        key, fields, idx = _parse_entry_body(text, body_start, close_delim)
        if key:
            entries.append(BibEntry(key, entry_type, fields))
    return entries


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


def extract_citations_from_source(source: Source) -> list[CitationOccurrence]:
    """Extract citation occurrences and existing check statuses from a source."""
    tokens = scan(source.text)
    citations: list[CitationOccurrence] = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token.kind != "command" or token.value not in _CITATION_COMMANDS:
            idx += 1
            continue

        cmd = token.value
        line = source.line_number(token.start)
        col = token.start - source.offset_of(line, 1) + 1
        keys, idx = _parse_citation_keys_at(tokens, idx + 1)

        line_start = source.offset_of(line, 1)
        line_end = source.text.find("\n", line_start)
        line_text = source.text[line_start : len(source.text) if line_end == -1 else line_end].rstrip("\r")

        for k in keys:
            status = _parse_comment_status(line_text, k)
            citations.append(CitationOccurrence(k, source.filename, line, col, cmd, line_text, status))

    return citations


def extract_citations_from_project(root_path: Path) -> list[CitationOccurrence]:
    """Extract citations across all tex files reachable from root_path."""
    if root_path.is_file() and root_path.suffix == ".tex":
        doc = load_document(root_path)
        citations: list[CitationOccurrence] = []
        for src in doc.sources:
            citations.extend(extract_citations_from_source(src))
        return citations

    search_dir = root_path if root_path.is_dir() else root_path.parent
    citations = []
    for tex_file in sorted(search_dir.rglob("*.tex")):
        with tex_file.open(encoding="utf-8", newline="") as handle:
            src = Source(str(tex_file), handle.read())
        citations.extend(extract_citations_from_source(src))
    return citations


def _parse_bib_file(path: Path) -> dict[str, BibEntry]:
    """Parse a single BibTeX file and return map of keys to entries."""
    with path.open(encoding="utf-8", newline="") as handle:
        return {entry.key: entry for entry in parse_bibtex(handle.read())}


def load_bib_entries_from_project(root_path: Path, explicit_bib: Path | None = None) -> dict[str, BibEntry]:
    """Load BibTeX entries from project bibliography files or explicit path."""
    if explicit_bib is not None:
        return _parse_bib_file(explicit_bib)

    if root_path.is_file():
        if root_path.suffix == ".bib":
            return _parse_bib_file(root_path)
        doc = load_document(root_path)
        entries: dict[str, BibEntry] = {}
        for bib_node in doc.bib_nodes:
            for entry in parse_bibtex(bib_node.source.text):
                entries[entry.key] = entry
        if entries:
            return entries

    search_dir = root_path if root_path.is_dir() else root_path.parent
    entries = {}
    for bib_file in sorted(search_dir.rglob("*.bib")):
        entries.update(_parse_bib_file(bib_file))
    return entries


def _resolve_bib_file_field(file_field: str, references_dir: Path) -> Path | None:
    """Resolve file paths extracted from a BibTeX file field."""
    candidates: list[str] = []
    for part in file_field.split(";"):
        cleaned = part.strip()
        if cleaned.startswith(":"):
            subparts = cleaned.split(":")
            candidates.extend(sub for sub in subparts if sub.lower().endswith(".pdf"))
        else:
            candidates.append(cleaned)

    for candidate in candidates:
        cand_path = Path(candidate)
        if cand_path.is_file():
            return cand_path
        if (references_dir / cand_path).is_file():
            return references_dir / cand_path
        if (references_dir.parent / cand_path).is_file():
            return references_dir.parent / cand_path
    return None


def resolve_reference_pdf(key: str, bib_entry: BibEntry | None, references_dir: Path) -> Path | None:
    """Locate existing PDF file for a citation key in references directory or from bib fields."""
    direct_path = references_dir / f"{key}.pdf"
    if direct_path.is_file():
        return direct_path

    if bib_entry is not None and bib_entry.file:
        return _resolve_bib_file_field(bib_entry.file, references_dir)

    return None


def _download_pdf(url: str, dest_path: Path, client: httpx.Client) -> bool:
    """Download a PDF from a URL, writing to dest_path if valid."""
    try:
        resp = client.get(
            url,
            follow_redirects=True,
            timeout=20.0,
            headers={"User-Agent": _USER_AGENT},
        )
        if resp.status_code == http.HTTPStatus.OK:
            content = resp.content
            content_type = resp.headers.get("content-type", "").lower()
            if content.startswith(b"%PDF") or ("pdf" in content_type and b"%PDF" in content[:1024]):
                dest_path.write_bytes(content)
                return True
    except (httpx.RequestError, OSError):
        return False
    return False


def _try_download_arxiv(arxiv_id: str, dest_path: Path, client: httpx.Client) -> bool:
    """Attempt download from arXiv given an arXiv ID."""
    clean_id = arxiv_id.strip()
    if clean_id.lower().startswith("arxiv:"):
        clean_id = clean_id[6:].strip()
    url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    return _download_pdf(url, dest_path, client)


def _try_unpaywall(doi: str, dest_path: Path, client: httpx.Client) -> bool:
    """Attempt download from Unpaywall given a DOI across all available OA locations."""
    unpaywall_url = f"https://api.unpaywall.org/v2/{doi}?email={_UNPAYWALL_EMAIL}"
    try:
        resp = client.get(unpaywall_url, timeout=15.0, headers={"User-Agent": _USER_AGENT})
        if resp.status_code == http.HTTPStatus.OK:
            data = resp.json()
            best_oa = data.get("best_oa_location") or {}
            best_pdf = best_oa.get("url_for_pdf")
            if best_pdf and _download_pdf(best_pdf, dest_path, client):
                return True

            for loc in data.get("oa_locations", []):
                pdf_url = loc.get("url_for_pdf")
                if not pdf_url and loc.get("url", "").lower().endswith(".pdf"):
                    pdf_url = loc.get("url")
                if pdf_url and pdf_url != best_pdf and _download_pdf(pdf_url, dest_path, client):
                    return True
    except (httpx.RequestError, ValueError, KeyError):
        pass
    return False


def _rate_limit_semantic_scholar() -> None:
    """Ensure at least one second elapses between Semantic Scholar requests."""
    global _last_s2_request_time  # noqa: PLW0603 -- module-level rate limit timestamp across calls
    now = time.monotonic()
    elapsed = now - _last_s2_request_time
    if 0.0 <= elapsed < _S2_MIN_REQUEST_INTERVAL:
        time.sleep(_S2_MIN_REQUEST_INTERVAL - elapsed)
    _last_s2_request_time = time.monotonic()


def _try_semantic_scholar(doi: str, dest_path: Path, client: httpx.Client) -> bool:
    """Attempt rate-limited download from Semantic Scholar for a DOI, checking OA link and ArXiv."""
    s2_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf,externalIds"
    try:
        _rate_limit_semantic_scholar()
        resp = client.get(s2_url, timeout=15.0, headers={"User-Agent": _USER_AGENT})
        if resp.status_code == http.HTTPStatus.OK:
            data = resp.json()
            oa_pdf = data.get("openAccessPdf")
            if oa_pdf and oa_pdf.get("url") and _download_pdf(oa_pdf["url"], dest_path, client):
                return True
            arxiv_id = data.get("externalIds", {}).get("ArXiv")
            if arxiv_id and _try_download_arxiv(arxiv_id, dest_path, client):
                return True
    except (httpx.RequestError, ValueError, KeyError):
        pass
    return False


def _try_semantic_scholar_search(title: str, dest_path: Path, client: httpx.Client) -> bool:
    """Attempt rate-limited download using Semantic Scholar paper search by title."""
    clean_title = re.sub(r"[{}]", "", title).strip()
    if len(clean_title) < _MIN_SEARCH_TITLE_LEN:
        return False
    s2_search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    try:
        _rate_limit_semantic_scholar()
        resp = client.get(
            s2_search_url,
            params={"query": clean_title, "limit": 1, "fields": "openAccessPdf,externalIds,title"},
            timeout=15.0,
            headers={"User-Agent": _USER_AGENT},
        )
        if resp.status_code == http.HTTPStatus.OK:
            data = resp.json()
            papers = data.get("data", [])
            if not papers:
                return False
            paper = papers[0]
            oa_pdf = paper.get("openAccessPdf")
            if oa_pdf and oa_pdf.get("url") and _download_pdf(oa_pdf["url"], dest_path, client):
                return True
            arxiv_id = paper.get("externalIds", {}).get("ArXiv")
            if arxiv_id and _try_download_arxiv(arxiv_id, dest_path, client):
                return True
            discovered_doi = paper.get("externalIds", {}).get("DOI")
            if discovered_doi and _try_unpaywall(discovered_doi, dest_path, client):
                return True
    except (httpx.RequestError, ValueError, KeyError):
        pass
    return False


def _try_download_doi(doi: str, dest_path: Path, client: httpx.Client) -> bool:
    """Attempt open access PDF retrieval for a DOI using Unpaywall and Semantic Scholar."""
    clean_doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "http://dx.doi.org/", "doi:"):
        if clean_doi.lower().startswith(prefix):
            clean_doi = clean_doi[len(prefix) :].strip()

    if clean_doi.lower().startswith("10.48550/arxiv."):
        arxiv_id = clean_doi.split("10.48550/arxiv.", 1)[1]
        return _try_download_arxiv(arxiv_id, dest_path, client)

    return _try_unpaywall(clean_doi, dest_path, client) or _try_semantic_scholar(clean_doi, dest_path, client)


def _try_download_bib_entry(entry: BibEntry, dest_pdf: Path, client: httpx.Client) -> bool:
    """Attempt downloading reference PDF for a BibEntry across available endpoints."""
    if entry.eprint and _try_download_arxiv(entry.eprint, dest_pdf, client):
        return True
    if entry.doi and _try_download_doi(entry.doi, dest_pdf, client):
        return True
    if entry.url and (entry.url.endswith(".pdf") or "/pdf" in entry.url) and _download_pdf(entry.url, dest_pdf, client):
        return True
    return bool(entry.title and _try_semantic_scholar_search(entry.title, dest_pdf, client))


def fetch_missing_references(
    citations: Sequence[CitationOccurrence],
    bib_entries: dict[str, BibEntry],
    references_dir: Path,
    *,
    client: httpx.Client | None = None,
    force: bool = False,
) -> FetchResult:
    """Download missing reference PDFs for cited keys into references_dir."""
    references_dir.mkdir(parents=True, exist_ok=True)
    keys_to_check = {c.key for c in citations} if citations else set(bib_entries.keys())

    existing: list[tuple[str, Path]] = []
    downloaded: list[tuple[str, Path]] = []
    unretrieved: list[UnretrievedRef] = []

    owned_client = False
    if client is None:
        client = httpx.Client()
        owned_client = True

    try:
        for key in sorted(keys_to_check):
            entry = bib_entries.get(key)
            existing_path = resolve_reference_pdf(key, entry, references_dir)
            if existing_path is not None and not force:
                existing.append((key, existing_path))
                continue

            dest_pdf = references_dir / f"{key}.pdf"
            if entry is not None and _try_download_bib_entry(entry, dest_pdf, client):
                downloaded.append((key, dest_pdf))
            else:
                unretrieved.append(
                    UnretrievedRef(
                        key=key,
                        title=entry.title if entry else "",
                        author=entry.author if entry else "",
                        doi=entry.doi if entry else "",
                        url=entry.url if entry else "",
                        reason="Paywalled or no open access PDF found",
                    )
                )
    finally:
        if owned_client:
            client.close()

    return FetchResult(tuple(downloaded), tuple(unretrieved), tuple(existing))


def extract_reference_texts(references_dir: Path, output_dir: Path, *, force: bool = False) -> list[Path]:
    """Extract page-annotated text from PDFs in references directory into output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_paths: list[Path] = []
    pdf_files = sorted(references_dir.glob("*.pdf"))

    for pdf_path in pdf_files:
        out_txt = output_dir / f"{pdf_path.stem}.txt"
        if out_txt.exists() and not force:
            extracted_paths.append(out_txt)
            continue

        try:
            reader = pypdf.PdfReader(str(pdf_path))
            pages_text: list[str] = []
            for page_num, page in enumerate(reader.pages, start=1):
                page_content = page.extract_text() or ""
                pages_text.append(f"=== Page {page_num} ===\n{page_content.strip()}\n")
            out_txt.write_text("\n".join(pages_text), encoding="utf-8")
            extracted_paths.append(out_txt)
        except Exception as err:  # noqa: BLE001 -- record failure gracefully in text file
            out_txt.write_text(f"=== Error reading PDF ===\n{err}\n", encoding="utf-8")
            extracted_paths.append(out_txt)

    return extracted_paths
