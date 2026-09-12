---
name: citation-checker
description: Audit citations in LaTeX documents, download missing reference papers, verify claims against paper content, and mark text with verification comments.
disable-model-invocation: false
---

# Citation checker

Verify that claims in LaTeX drafts are accurately and faithfully substantiated by cited literature.

## Workflow

1. **Fetch and prepare reference papers**:
   - Run `uv run latex-lint refs fetch`.
   - The tool searches open-access sources (arXiv, Unpaywall, Semantic Scholar, direct URLs) and saves downloaded papers to `references/<citekey>.pdf`.
   - If any papers cannot be downloaded automatically due to paywalls or missing DOI/URL fields:
     - The tool prints a table of unresolved references.
     - Prompt the user to manually place the missing PDFs into `references/<citekey>.pdf` before proceeding.
   - Run `uv run latex-lint refs extract` to convert PDFs into page-annotated text under `.latex_lint/references_text/`.

2. **Locate in-text citations**:
   - Run `uv run latex-lint check --rule CITE-09 <root>` to immediately locate all in-text citations lacking a `% cite-checked:` comment.
   - For incremental verification, check existing citation comments:
     - If already marked `% cite-checked: SUPPORTED`, skip it unless `--force` was requested.
     - If marked with a negative or unresolved status, or flagged by `CITE-09` as never checked, proceed with verification.

3. **Determine claim scope**:
   - Dynamically identify the scope of the claim being supported by the citation from the surrounding context (a specific clause, the full sentence, or the enclosing paragraph).

4. **Verify claim against extracted paper**:
   - Inspect `.latex_lint/references_text/<citekey>.txt`.
   - Search for key concepts, experimental numbers, definitions, or findings relevant to the claim.
   - Assign one of four verdicts:
     - `SUPPORTED`: The paper explicitly validates, proves, or states the assertion.
     - `NUANCED`: The paper supports the assertion only under specific caveats, limits, or conditions omitted in the LaTeX text.
     - `CONTRADICTED`: The paper's findings or statements contradict what is asserted.
     - `NOT_FOUND`: The paper does not contain or mention the claimed result or parameter.
   - Pinpoint the exact location in the paper (Page number, Section / Theorem / Table / Figure) and extract a concise verbatim quote.

5. **Annotate LaTeX source**:
   - Add a trailing comment strictly at the end of the line containing the citation:
     - Single citation:

       ```latex
       Recent advances demonstrate linear convergence~\cite{smith2020}. % cite-checked: SUPPORTED
       ```

     - Multi-citation:

       ```latex
       Several algorithms exist~\cite{smith2020, doe2021}. % cite-checked: smith2020=SUPPORTED, doe2021=NOT_FOUND
       ```

     - Negative verdict:

       ```latex
       The system reaches 99\% accuracy~\cite{doe2021}. % cite-checked: CONTRADICTED
       ```

   - Ensure the comment never begins with `% latex-lint:` so it does not interfere with linting directives.

6. **Generate audit report**:
   - Compile or update `CITATION_AUDIT.md` in the project root with the compact table format:

     ```markdown
     # Citation Audit Report

     | File:Line | Citation Key | Status | Paper Location | Notes / Verbatim Evidence |
     |-----------|--------------|--------|----------------|---------------------------|
     | intro.tex:42 | smith2020 | SUPPORTED | p. 4, Sec. 3.2 | "We observed linear convergence across..." |
     | intro.tex:58 | doe2021 | NOT_FOUND | N/A | No mention of 99% accuracy in text or tables |
     ```

   - Highlight any `CONTRADICTED`, `NOT_FOUND`, or `NUANCED` claims to the user for immediate attention.
