from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter

from latex_linting.cli import main
from latex_linting.refs import (
    BibEntry,
    CitationOccurrence,
    _rate_limit_semantic_scholar,
    extract_citations_from_source,
    extract_reference_texts,
    fetch_missing_references,
    parse_bibtex,
    resolve_reference_pdf,
)
from latex_linting.skills_install import install_skills
from latex_linting.source import Source


def test_parse_bibtex_extracts_entries_and_fields() -> None:
    bib_text = """
    % Some comment
    @article{smith2020,
      title = {A Great Paper on {AI}},
      author = {John Smith and Jane Doe},
      journal = {Journal of Testing},
      year = {2020},
      doi = {10.1000/182},
      url = {https://example.com/smith2020.pdf},
      eprint = {2001.00001},
      file = {references/custom_smith.pdf}
    }

    @inproceedings{doe2021,
      title = "Another Study",
      author = "Jane Doe",
      year = "2021"
    }
    """
    entries = parse_bibtex(bib_text)
    assert len(entries) == 2

    e1 = entries[0]
    assert e1.key == "smith2020"
    assert e1.entry_type == "article"
    assert e1.title == "A Great Paper on {AI}"
    assert e1.author == "John Smith and Jane Doe"
    assert e1.doi == "10.1000/182"
    assert e1.url == "https://example.com/smith2020.pdf"
    assert e1.eprint == "2001.00001"
    assert e1.file == "references/custom_smith.pdf"

    e2 = entries[1]
    assert e2.key == "doe2021"
    assert e2.entry_type == "inproceedings"
    assert e2.title == "Another Study"
    assert e2.doi == ""


def test_extract_citations_from_source_finds_commands_and_comments() -> None:
    tex_content = (
        "We consider deep learning \\cite{smith2020}. % cite-checked: SUPPORTED\n"
        "Earlier methods failed \\citep[see][p.~4]{doe2021, baker2022}. % cite-checked: doe2021=SUPPORTED, baker2022=NOT_FOUND\n"
        "Unchecked statement \\citet{miller2023}.\n"
        "% latex-lint:ignore=PROSE-01\n"
        "Another sentence with \\autocite{new2024}.\n"
    )
    source = Source("chapter1.tex", tex_content)
    citations = extract_citations_from_source(source)

    assert len(citations) == 5

    c0 = citations[0]
    assert c0.key == "smith2020"
    assert c0.line == 1
    assert c0.command == "\\cite"
    assert c0.status == "SUPPORTED"

    c1 = citations[1]
    assert c1.key == "doe2021"
    assert c1.line == 2
    assert c1.status == "SUPPORTED"

    c2 = citations[2]
    assert c2.key == "baker2022"
    assert c2.line == 2
    assert c2.status == "NOT_FOUND"

    c3 = citations[3]
    assert c3.key == "miller2023"
    assert c3.line == 3
    assert c3.status is None

    c4 = citations[4]
    assert c4.key == "new2024"
    assert c4.line == 5
    assert c4.status is None


def test_resolve_reference_pdf(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    # 1. Existing in references/<key>.pdf
    p1 = refs_dir / "smith2020.pdf"
    p1.write_bytes(b"%PDF-1.4 smith")

    resolved = resolve_reference_pdf("smith2020", None, refs_dir)
    assert resolved == p1

    # 2. Existing via .bib file attribute
    custom_pdf = tmp_path / "custom.pdf"
    custom_pdf.write_bytes(b"%PDF-1.4 custom")
    entry = BibEntry("doe2021", "article", {"file": str(custom_pdf)})

    resolved_custom = resolve_reference_pdf("doe2021", entry, refs_dir)
    assert resolved_custom == custom_pdf

    # 3. Not found
    assert resolve_reference_pdf("absent2022", None, refs_dir) is None


def test_extract_reference_texts(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()
    out_dir = tmp_path / "out_text"

    # Create a small valid 2-page PDF
    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=100, height=100)
    pdf_writer.add_blank_page(width=100, height=100)
    pdf_file = refs_dir / "paper1.pdf"
    with pdf_file.open("wb") as handle:
        pdf_writer.write(handle)

    extracted = extract_reference_texts(refs_dir, out_dir)
    assert len(extracted) == 1
    assert extracted[0].name == "paper1.txt"

    content = extracted[0].read_text(encoding="utf-8")
    assert "=== Page 1 ===" in content
    assert "=== Page 2 ===" in content

    # Should skip on second run without force
    extracted2 = extract_reference_texts(refs_dir, out_dir, force=False)
    assert len(extracted2) == 1


def test_fetch_missing_references_arxiv(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    bib_entry = BibEntry("arxiv2023", "article", {"eprint": "2301.12345", "title": "Arxiv Paper"})
    occ = CitationOccurrence("arxiv2023", "doc.tex", 1, 1, "\\cite", "text", None)

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b"%PDF-1.5 fake pdf content"
    mock_resp.headers = {"content-type": "application/pdf"}
    mock_client.get.return_value = mock_resp

    result = fetch_missing_references([occ], {"arxiv2023": bib_entry}, refs_dir, client=mock_client)

    assert len(result.downloaded) == 1
    assert result.downloaded[0][0] == "arxiv2023"
    assert (refs_dir / "arxiv2023.pdf").exists()
    assert (refs_dir / "arxiv2023.pdf").read_bytes() == b"%PDF-1.5 fake pdf content"


def test_fetch_missing_references_unretrieved(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    bib_entry = BibEntry("paywalled2020", "article", {"doi": "10.1016/j.fake.2020", "title": "Closed Paper"})
    occ = CitationOccurrence("paywalled2020", "doc.tex", 1, 1, "\\cite", "text", None)

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_client.get.return_value = mock_resp

    result = fetch_missing_references([occ], {"paywalled2020": bib_entry}, refs_dir, client=mock_client)

    assert len(result.downloaded) == 0
    assert len(result.unretrieved) == 1
    assert result.unretrieved[0].key == "paywalled2020"


def test_cli_refs_extract(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()
    out_dir = tmp_path / ".latex_lint" / "references_text"

    pdf_writer = PdfWriter()
    pdf_writer.add_blank_page(width=100, height=100)
    with (refs_dir / "testpaper.pdf").open("wb") as handle:
        pdf_writer.write(handle)

    code = main(["refs", "extract", str(tmp_path), "--references-dir", str(refs_dir), "--output-dir", str(out_dir)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Extracted text for 1 reference" in captured.out
    assert (out_dir / "testpaper.txt").exists()


def test_cli_refs_fetch(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    refs_dir = tmp_path / "references"
    bib_file = tmp_path / "main.bib"
    bib_file.write_text("@article{key1, title = {Title}, eprint = {2301.0001}}\n", encoding="utf-8")
    tex_file = tmp_path / "main.tex"
    tex_file.write_text("\\cite{key1}\n", encoding="utf-8")

    with patch("latex_linting.refs.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"%PDF-1.5 dummy"
        mock_resp.headers = {"content-type": "application/pdf"}
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        code = main(["refs", "fetch", str(tex_file), "--references-dir", str(refs_dir), "--bib", str(bib_file)])
        assert code == 0
        captured = capsys.readouterr()
        assert "Downloaded references: 1" in captured.out
        assert (refs_dir / "key1.pdf").exists()


def test_install_skills_includes_citation_checker(tmp_path: Path) -> None:
    dest = tmp_path / "skills"
    installed = install_skills(dest)
    names = [p.name for p in installed]
    assert "citation-checker" in names


def test_fetch_missing_references_unpaywall_secondary_location(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    bib_entry = BibEntry("multi2020", "article", {"doi": "10.1000/182", "title": "Paper Title"})
    occ = CitationOccurrence("multi2020", "doc.tex", 1, 1, "\\cite", "text", None)

    mock_client = MagicMock()
    # 1. Unpaywall API response: best_oa has broken link, secondary oa_location has valid pdf
    unpaywall_resp = MagicMock()
    unpaywall_resp.status_code = 200
    unpaywall_resp.json.return_value = {
        "best_oa_location": {"url_for_pdf": "https://broken.example.com/best.pdf"},
        "oa_locations": [
            {"url_for_pdf": "https://broken.example.com/best.pdf"},
            {"url_for_pdf": "https://mirror.example.com/good.pdf"},
        ],
    }

    pdf_resp_broken = MagicMock()
    pdf_resp_broken.status_code = 404

    pdf_resp_good = MagicMock()
    pdf_resp_good.status_code = 200
    pdf_resp_good.content = b"%PDF-1.4 good mirror content"
    pdf_resp_good.headers = {"content-type": "application/pdf"}

    def side_effect(url: object, **kwargs: object) -> MagicMock:
        if "api.unpaywall.org" in str(url):
            return unpaywall_resp
        if "broken" in str(url):
            return pdf_resp_broken
        if "mirror" in str(url):
            return pdf_resp_good
        return MagicMock(status_code=404)

    mock_client.get.side_effect = side_effect

    result = fetch_missing_references([occ], {"multi2020": bib_entry}, refs_dir, client=mock_client)
    assert len(result.downloaded) == 1
    assert (refs_dir / "multi2020.pdf").read_bytes() == b"%PDF-1.4 good mirror content"


def test_fetch_missing_references_title_search_fallback(tmp_path: Path) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    # Entry with NO DOI and NO eprint
    bib_entry = BibEntry("classic2004", "book", {"title": "{Convex} Optimization", "author": "Boyd"})
    occ = CitationOccurrence("classic2004", "doc.tex", 1, 1, "\\cite", "text", None)

    mock_client = MagicMock()
    s2_search_resp = MagicMock()
    s2_search_resp.status_code = 200
    s2_search_resp.json.return_value = {
        "data": [
            {
                "title": "Convex Optimization",
                "openAccessPdf": {"url": "https://stanford.edu/boyd.pdf"},
            }
        ]
    }

    pdf_resp = MagicMock()
    pdf_resp.status_code = 200
    pdf_resp.content = b"%PDF-1.5 convex optimization book"
    pdf_resp.headers = {"content-type": "application/pdf"}

    def side_effect(url: object, **kwargs: object) -> MagicMock:
        if "api.semanticscholar.org/graph/v1/paper/search" in str(url):
            return s2_search_resp
        if "stanford.edu" in str(url):
            return pdf_resp
        return MagicMock(status_code=404)

    mock_client.get.side_effect = side_effect

    result = fetch_missing_references([occ], {"classic2004": bib_entry}, refs_dir, client=mock_client)
    assert len(result.downloaded) == 1
    assert result.downloaded[0][0] == "classic2004"
    assert (refs_dir / "classic2004.pdf").read_bytes() == b"%PDF-1.5 convex optimization book"


def test_rate_limit_semantic_scholar_sleeps_on_rapid_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("latex_linting.refs._last_s2_request_time", 100.0)
    timestamps = iter([100.2, 101.0])
    monkeypatch.setattr("latex_linting.refs.time.monotonic", lambda: next(timestamps))

    sleep_mock = MagicMock()
    monkeypatch.setattr("latex_linting.refs.time.sleep", sleep_mock)

    _rate_limit_semantic_scholar()

    sleep_mock.assert_called_once()
    sleep_duration = sleep_mock.call_args[0][0]
    assert sleep_duration == pytest.approx(0.8, rel=1e-3)


def test_rate_limit_semantic_scholar_no_sleep_when_interval_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("latex_linting.refs._last_s2_request_time", 100.0)
    monkeypatch.setattr("latex_linting.refs.time.monotonic", lambda: 101.5)

    sleep_mock = MagicMock()
    monkeypatch.setattr("latex_linting.refs.time.sleep", sleep_mock)

    _rate_limit_semantic_scholar()

    sleep_mock.assert_not_called()


def test_fetch_missing_references_applies_rate_limiting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    refs_dir = tmp_path / "references"
    refs_dir.mkdir()

    e1 = BibEntry("paper1", "article", {"title": "First Paper Title", "author": "Alice"})
    e2 = BibEntry("paper2", "article", {"title": "Second Paper Title", "author": "Bob"})
    occ1 = CitationOccurrence("paper1", "doc.tex", 1, 1, "\\cite", "text", None)
    occ2 = CitationOccurrence("paper2", "doc.tex", 2, 1, "\\cite", "text", None)

    mock_client = MagicMock()
    mock_resp = MagicMock(status_code=404)
    mock_client.get.return_value = mock_resp

    sleep_mock = MagicMock()
    monkeypatch.setattr("latex_linting.refs.time.sleep", sleep_mock)
    # Simulate first call at 10.0 and second call at 10.1 (0.1s later)
    # Each rate limit check calls monotonic twice (before check and on timestamp update)
    clock = [10.0, 10.0, 10.1, 11.0]
    monkeypatch.setattr("latex_linting.refs.time.monotonic", lambda: clock.pop(0) if clock else 11.0)
    monkeypatch.setattr("latex_linting.refs._last_s2_request_time", 0.0)

    fetch_missing_references([occ1, occ2], {"paper1": e1, "paper2": e2}, refs_dir, client=mock_client)

    sleep_mock.assert_called_once()
    assert sleep_mock.call_args[0][0] == pytest.approx(0.9, rel=1e-3)
