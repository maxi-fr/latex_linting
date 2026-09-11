from pathlib import Path

import pytest

from latex_linting.cli import main as cli_main
from latex_linting.document import MissingIncludeError
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def test_cite_08_metadata() -> None:
    rule = get_rule("CITE-08")
    assert rule.rule_id == "CITE-08"
    assert "metadata" in rule.explanation.lower() or "field" in rule.explanation.lower()
    assert len(rule.passing_examples) >= 2
    assert len(rule.failing_examples) >= 2
    assert "doi" in rule.limits.lower()
    assert "isbn" in rule.limits.lower()


def test_cite_08_valid_entries(tmp_path: Path) -> None:
    bib = tmp_path / "references.bib"
    bib.write_text(
        r"""
@Comment{jabref-meta: databaseType:bibtex;}
@String{ieee = "IEEE"}
@Preamble{"Maintained by IAT"}

@article{smith2020,
  author = {Smith, John and Doe, Jane},
  title = {Advances in Control Theory},
  journal = {IEEE Transactions on Automatic Control},
  year = {2020},
  volume = {65},
  pages = {100--115},
  doi = {10.1109/TAC.2020.1234567},
}

@book{adamy2007,
  author = {Adamy, J{\"u}rgen},
  title = {Systemdynamik und Regelungstechnik II},
  publisher = {Shaker},
  year = {2007},
  isbn = {978-3-8322-6800-8},
}

@inproceedings{proc2019,
  author = {Alice Researcher},
  title = {Robust Estimation Under Noise},
  booktitle = {Proceedings of the European Control Conference},
  year = {2019},
  pages = {45--50},
  doi = {10.23919/ECC.2019.8795600},
}

@techreport{din1338,
  author = {{DIN 1338:1996-08}},
  title = {Formelschreibweise und Formelsatz},
  institution = {DIN Deutsches Institut f{\"u}r Normung},
  year = {1996},
}

@phdthesis{grad2021,
  author = {Max Mustermann},
  title = {Nonlinear Observers for Distributed Networks},
  school = {TU Darmstadt},
  year = {2021},
}

@manual{pgfplots,
  title = {Manual for Package PGFPLOTS},
  author = {Feuers{\"a}nger, Christian},
  year = {2011},
}

@misc{schmidt2003,
  author = {Walter Schmidt},
  title = {LaTeX2e-Kurzbeschreibung},
  year = {2003},
  url = {ftp://dante.ctan.org/tex-archive/info/lshort/},
}
""",
        encoding="utf-8",
    )

    findings = check(bib)
    assert [f for f in findings if f.rule_id == "CITE-08"] == []


def test_cite_08_article_missing_fields(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""@article{bad_article,
  author = {Smith, John},
  title = {Missing Venue Volume Pages DOI},
  year = {2020}
}
""",
        encoding="utf-8",
    )
    findings = check(bib)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    f = c8[0]
    assert f.filename == str(bib)
    assert f.line == 1
    assert f.column == 1
    assert "journal" in f.explanation
    assert "volume" in f.explanation
    assert "pages" in f.explanation
    assert "doi" in f.explanation


def test_cite_08_book_missing_isbn(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""@book{adamy_no_isbn,
  author = {Adamy, J{\"u}rgen},
  title = {Systemdynamik und Regelungstechnik II},
  publisher = {Shaker},
  year = {2007},
}
""",
        encoding="utf-8",
    )
    findings = check(bib)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    f = c8[0]
    assert f.line == 1
    assert "isbn" in f.explanation
    assert "isbn" in f.correction.lower()


def test_cite_08_book_with_doi_no_isbn_passes(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""@book{monograph_doi,
  author = {Smith, John},
  title = {Electronic Monograph},
  publisher = {Springer},
  year = {2021},
  doi = {10.1007/978-3-030-12345-6},
}
""",
        encoding="utf-8",
    )
    findings = check(bib)
    assert [f for f in findings if f.rule_id == "CITE-08"] == []


def test_cite_08_inproceedings_missing_doi_and_isbn(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""@inproceedings{conf_no_id,
  author = {Bob Author},
  title = {Conference Paper},
  booktitle = {International Conference on Robotics},
  year = {2022},
  pages = {12--18},
}
""",
        encoding="utf-8",
    )
    findings = check(bib)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    f = c8[0]
    assert "doi" in f.explanation or "isbn" in f.explanation


def test_cite_08_empty_field_counts_as_missing(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""@article{empty_fields,
  author = {Smith, John},
  title = {Test Article},
  journal = {Journal of Testing},
  year = {2020},
  volume = {},
  pages = "   ",
  doi = {}
}
""",
        encoding="utf-8",
    )
    findings = check(bib)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    f = c8[0]
    assert "volume" in f.explanation
    assert "pages" in f.explanation
    assert "doi" in f.explanation


def test_cite_08_discovery_via_addbibresource(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    bib = tmp_path / "literature.bib"

    root.write_text(
        r"""\documentclass{report}
\addbibresource{literature.bib}
\begin{document}
Citing here~\cite{bad_ref}.
\end{document}
""",
        encoding="utf-8",
    )

    bib.write_text(
        r"""@book{bad_ref,
  author = {Author, A.},
  title = {A Book Without Publisher or ISBN},
  year = {2020},
}
""",
        encoding="utf-8",
    )

    findings = check(root)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    assert Path(c8[0].filename).name == "literature.bib"
    assert "publisher" in c8[0].explanation
    assert "isbn" in c8[0].explanation


def test_cite_08_discovery_via_bibliography_without_extension(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    bib = tmp_path / "mylib.bib"

    root.write_text(
        r"""\documentclass{report}
\begin{document}
Text~\cite{entry1}.
\bibliography{mylib}
\end{document}
""",
        encoding="utf-8",
    )

    bib.write_text(
        r"""@book{entry1,
  author = {Author, B.},
  title = {Another Book},
  year = {2021},
}
""",
        encoding="utf-8",
    )

    findings = check(root)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    assert Path(c8[0].filename).name == "mylib.bib"


def test_cite_08_discovery_comma_separated_bibliography(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    bib1 = tmp_path / "lib1.bib"
    bib2 = tmp_path / "lib2.bib"

    root.write_text(
        r"""\documentclass{report}
\begin{document}
Text~\cite{e1, e2}.
\bibliography{lib1, lib2}
\end{document}
""",
        encoding="utf-8",
    )

    bib1.write_text(
        r"""@book{e1,
  author = {Author, One},
  title = {Book One},
  year = {2021},
}
""",
        encoding="utf-8",
    )

    bib2.write_text(
        r"""@book{e2,
  author = {Author, Two},
  title = {Book Two},
  year = {2022},
}
""",
        encoding="utf-8",
    )

    findings = check(root)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 2
    reported_files = {Path(f.filename).name for f in c8}
    assert reported_files == {"lib1.bib", "lib2.bib"}


def test_cite_08_missing_bib_file_raises_error(tmp_path: Path) -> None:
    root = tmp_path / "main.tex"
    root.write_text(
        r"""\documentclass{report}
\addbibresource{nonexistent.bib}
\begin{document}
Text.
\end{document}
""",
        encoding="utf-8",
    )

    with pytest.raises(MissingIncludeError, match=r"nonexistent\.bib"):
        check(root)

    assert cli_main(["check", str(root)]) == 2


def test_cite_08_suppressions(tmp_path: Path) -> None:
    bib = tmp_path / "refs.bib"
    bib.write_text(
        r"""% latex-lint: disable=CITE-08
@book{disabled_entry,
  author = {Author, C.},
  title = {Disabled Book},
  year = {2020},
}
% latex-lint: enable=CITE-08

@book{ignored_entry, % latex-lint: ignore=CITE-08
  author = {Author, D.},
  title = {Ignored Book},
  year = {2020},
}

@book{reported_entry,
  author = {Author, E.},
  title = {Reported Book},
  year = {2020},
}
""",
        encoding="utf-8",
    )

    findings = check(bib)
    c8 = [f for f in findings if f.rule_id == "CITE-08"]
    assert len(c8) == 1
    assert "reported_entry" in c8[0].explanation

    # Invocation-wide ignore
    findings_ignored = check(bib, ignored_rules=["CITE-08"])
    assert [f for f in findings_ignored if f.rule_id == "CITE-08"] == []


def test_cite_08_cli_rule_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli_main(["rule", "CITE-08"]) == 0
    out = capsys.readouterr().out
    assert "CITE-08:" in out
    assert "Passing examples:" in out
    assert "Failing examples:" in out
    assert "Detection limits:" in out
