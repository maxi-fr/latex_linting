# Thesis Guidelines and Linting Rules

This document synthesizes all guidelines and instructions from the IAT thesis guidelines (*Hinweise zum Verfassen einer (Abschluss-)Arbeit am IAT*) and the thesis `AGENTS.md`.

Primary source documents are preserved in this repository under:

- Thesis agent instructions: [thesis_AGENTS.md](docs/sources/thesis_AGENTS.md)
- IAT guidelines: [docs/sources/iat/](docs/sources/iat/) (including [thesisinfo.tex](docs/sources/iat/thesisinfo.tex), [literature.bib](docs/sources/iat/literature.bib), and section files in [inc/](docs/sources/iat/inc/))

Each point is ordered within its domain and tagged with its enforcement layer:

- `[Regex Linter]`: Deterministic mechanical rule checkable via Python regex and AST parsing.
- `[Review Agent]`: Semantic, structural, or contextual rule checked by an LLM review agent.
- `[Writing Skill]`: Prescriptive rule guiding draft generation by writing agents.

---

## 1. Document Structure and Hierarchy

### STRUC-01: Standard Thesis Document Structure

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Follow the prescribed academic structural sequence:
  1. Title page (Thesis type, title, author, submission date).
  2. Task assignment (*Aufgabenstellung* from supervisor).
  3. Declaration of originality (*Selbstständigkeitserklärung* using current legal wording).
  4. Abstract (German *Kurzfassung* and English *Abstract* fitting together on a single page).
  5. Table of contents (`\tableofcontents`).
  6. Symbols and abbreviations list (*Formelzeichen und Abkürzungen*).
  7. Main body (Intro, State of the Art, Methodology, Implementation, Results, Discussion, Conclusion).
  8. Appendix (Lengthy derivations, datasheets, code fragments).
  9. Bibliography (`biblatex` + `biber`).
  10. Separate project archive (Complete runnable code, CAD models, raw data).
- **Source**: IAT *Tipps.tex*, *Hinweise_LaTeX.tex*.
- **Review Criteria**: Check presence and ordering of all required sections in the root `.tex` file.

### STRUC-02: Maximum Chapter Nesting Depth

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Nest sections no deeper than three numerical levels (`1.2.3`, i.e., `\chapter`, `\section`, `\subsection`). Do not use `\subsubsection` or `\paragraph` with numerical heading counters.
- **Source**: `AGENTS.md` (Structure); IAT *Hinweise_Allgemein.tex*.
- **Regex Pattern**: `\\subsubsection\{` or deeper sectioning macros in main matter.
- **Review Criteria**: Flag any heading nested past three levels.

### STRUC-03: Rule of Subheadings (Minimum Two Per Level)

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: If a section is divided into subsections, there must be at least two subsections on that level (never an isolated `1.2.1` without a `1.2.2`).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Gliederung).
- **Regex / Parsing**: Parse heading hierarchy. Count children for each parent. Flag if child count is 1.

### STRUC-04: Narrative Problem-Solving Arc

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Tell the story of the problem and its solution rather than dumping an inventory of technical facts like a status report.
- **Source**: `AGENTS.md` (Structure); IAT *Tipps.tex*, *Beurteilung.tex*.
- **Review Criteria**: Ensure each chapter frames motivation, trade-offs, and conceptual steps rather than merely listing completed steps.

### STRUC-05: Mandatory Section Transitions

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Bridge every section into the next with a transition sentence or paragraph. A reader must never land in a new section without knowing why it follows the preceding one.
- **Source**: `AGENTS.md` (Structure).
- **Review Criteria**: Check the opening paragraph of each section for an explicit link to the previous section or overarching thesis goal.

### STRUC-06: Clean Section Terminations

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: End every chapter, section, subsection, and subsubsection on prose, never on an equation, list, table, or figure.
- **Source**: `AGENTS.md` (Structure).
- **Regex Pattern**: `\\end\{(equation|align|gather|table|figure|itemize|enumerate)\*?\}\s*(?=(\\(sub)*section|\\chapter|\\end\{document\}|\Z))`
- **Review Criteria**: Ensure the final block before any new heading is a complete prose sentence.

### STRUC-07: Conclusion Scope and Outlook

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: State no new results in the conclusion. The conclusion must only summarize key findings, synthesize insights, and provide an outlook on future work.
- **Source**: `AGENTS.md` (Structure); IAT *Zusammenfassung.tex*.
- **Review Criteria**: Verify that all statements and data in the conclusion refer back to previously discussed results.

---

## 2. Prose, Grammar, and Scientific Style

### PROSE-01: Concise and Active Prose (POEM Principle)

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Write according to POEM: Prägnanz (conciseness), Ordnung (logical structure), Einfachheit (simplicity), Motivation (purpose-driven). Clarity beats stylistic ornamentation. Keep sentences focused; split multi-clause run-ons.
- **Source**: IAT *Tipps.tex*, *Hinweise_Allgemein.tex* (sec:Stilistische Punkte).
- **Review Criteria**: Flag sentences exceeding 35 words or containing deeply nested subordinate clauses.

### PROSE-02: Forbid Standalone "This"

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Never let "This" or "These" stand alone as a grammatical subject or object. Always name the referent noun: "This method...", "This result...", not "This shows...".
- **Source**: `AGENTS.md` (Prose).
- **Regex Pattern**: `(?<=\.|\?|!|^)\s*This\s+(is|shows|demonstrates|indicates|leads|means|suggests|illustrates|proves|has|was|will)\b`
- **Review Criteria**: Flag occurrences of bare demonstrative pronouns acting as subject.

### PROSE-03: Restrictive "That" Without Comma

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: In English, do not place a comma before a restrictive clause introduced by "that".
- **Source**: `AGENTS.md` (Prose).
- **Regex Pattern**: `,\s+that\b`
- **Review Criteria**: Flag `, that` in running text (distinguish from idioms like "given that", "provided that", or non-restrictive parentheticals).

### PROSE-04: American Headline Capitalization in Headings

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: Use American headline case for titles and headings (e.g., "A Really Awesome Thesis", "Closed-Loop Deep Brain Stimulation").
- **Source**: `AGENTS.md` (Titles and headings).
- **Regex Pattern**: Check `\chapter{...}`, `\section{...}`, `\subsection{...}`. Verify major words are capitalized and minor function words (a, an, the, and, but, or, for, in, on, at, to) are lowercase unless starting the title.

### PROSE-05: Consistent Terminology (Ban Synonym Cycling)

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Always use the identical term for the same concept, variable, or component throughout the thesis. Do not vary technical names for literary variety.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Stilistische Punkte); `unslop`.
- **Review Criteria**: Check for alternating synonyms across chapters (e.g. interchanging "setpoint", "reference signal", "command variable").

### PROSE-06: Negative Results Analysis

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: When an approach fails or underperforms, provide a rigorous analysis explaining why the approach failed. Never sweep negative results under the rug.
- **Source**: IAT *Tipps.tex* (Inhalt und Umfang der Arbeit).
- **Review Criteria**: Ensure failed trials or rejected hypotheses include failure mechanisms, parametric limits, or root-cause explanations.

### PROSE-07: Grammatical Integration of Equations

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: Fold displayed equations into the grammatical syntax of the surrounding sentence. Never place a colon immediately before a displayed equation.
- **Source**: `AGENTS.md` (Prose); IAT *Hinweise_Allgemein.tex* (sec:Latex-Gliederung, Mathematische Formeln).
- **Regex Pattern**: `:\s*\n*\s*\\begin\{(equation|align|gather)\*?\}`
- **Review Criteria**: Ensure the sentence reads naturally through the equation, ending with appropriate terminal punctuation.

### PROSE-08: Eliminate AI Tells and Slop

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Follow the `/unslop` skill. Cut puffery ("pivotal", "deeply rooted", "testament to"), avoid superficial "-ing" clauses ("highlighting...", "ensuring..."), replace AI vocabulary ("delve", "crucial", "landscape", "tapestry"), and eliminate em dashes.
- **Source**: `AGENTS.md` (Prose); `unslop` skill.
- **Review Criteria**: Search for banned AI vocabulary words, promotional tone, and robotic formulaic transitions.

---

## 3. Claims, Citations, and Plagiarism

### CITE-01: Universal Substantiation of Claims

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Back every assertion, premise, or parameter choice with a citation, proof, or experimental data. Standard textbook steps need only a recognized keyword ("follows by integration by parts").
- **Source**: `AGENTS.md` (Claims and citations); IAT *Hinweise_Allgemein.tex* (sec:Latex-Zitieren).
- **Review Criteria**: Flag unbacked empirical claims, unreferenced state-of-the-art assertions, or arbitrary numerical parameters.

### CITE-02: Paraphrasing over Direct Quotation

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Paraphrase source material into your own words. Literal quotations are rare in engineering and science.
- **Source**: `AGENTS.md` (Claims and citations); IAT *Hinweise_Allgemein.tex*.
- **Review Criteria**: Flag blocks of quoted text unless analyzing historical, legal, or normative verbatim phrasing.

### CITE-03: Verbatim Quotation Rules

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: If a direct quote is strictly necessary, transcribe it character-by-character in quotation marks, label source errors with `(sic!)`, and explicitly credit translations ("(translated from ... by author)").
- **Source**: IAT *Hinweise_Allgemein.tex*, *Anhang.tex*.
- **Review Criteria**: Check that quoted material contains quotation marks, citation, and attribution.

### CITE-04: Precise Citation Placement and Scope

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Place `\cite` immediately adjacent to the specific clause it supports. If at the end of a sentence, place the citation before the terminal period: `...~\cite{ref}.`
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Zitieren).
- **Regex Pattern**: Flag trailing citations where the period precedes `\cite`: `\.\s*\\cite\{`
- **Review Criteria**: Ensure the reader can distinguish the author's contribution from the cited work.

### CITE-05: Common Knowledge Boundary

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Apply the MIT common knowledge test: would a fellow student at your academic stage know this fact without looking it up? Basic calculus and Ohm's law need no citation; specialized theorems, lookup tables, and controller tuning formulas require citations.
- **Source**: IAT *Hinweise_Allgemein.tex* (Grundwissen).
- **Review Criteria**: Ensure foundational material is not over-cited while specialized techniques are properly attributed.

### CITE-06: Reliable Source Selection Hierarchy

- **Layer**: `[Review Agent]`
- **Rule**: Prioritize peer-reviewed journal articles, conference papers, textbooks, and dissertations. Avoid Wikipedia and transient URLs. If a web source is necessary, document URL, exact retrieval date, and archive a digital copy.
- **Source**: IAT *Hinweise_Allgemein.tex* (Zitierfähigkeit).
- **Regex / BibTeX Criteria**: In `.bib`, flag entries with `url` missing `urldate`, or entries citing Wikipedia.

### CITE-07: In-Text Citation Precision

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: When citing extensive works (books, monographs, long standards), provide specific page, chapter, or theorem numbers: `\cite[p.~123]{author2020}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (Quellenverweise im Text).
- **Review Criteria**: Check that book citations provide page-level pinning for verification.

### CITE-08: Complete Bibliography Metadata

- **Layer**: `[Regex Linter]`
- **Rule**: Every bibliography entry in the `.bib` file must contain complete fields: author(s), title, publication venue (journal, conference, publisher), year, volume, page range, and DOI or ISBN where available.
- **Source**: IAT *Anhang.tex*, *Hinweise_Allgemein.tex*.
- **Review Criteria**: Scan `.bib` for entries missing mandatory BibLaTeX fields.

---

## 4. Mathematics and Formulas

### MATH-01: Grammatically Integrated Math Punctuation

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Every displayed formula is part of a sentence and must terminate with punctuation (comma, semicolon, or period) separated from the math by a thin space `\,`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Mathematische Formeln); `AGENTS.md`.
- **Regex Pattern**: Check math environments (`equation`, `align`, `gather`) for missing punctuation before `\end{...}`: `(?<!\\\,[\.,;])\s*\\end\{(equation|align|gather)\*?\}`
- **Review Criteria**: Verify displayed formulas are followed by grammatically appropriate punctuation.

### MATH-02: Conditional Equation Numbering

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: Number an equation only if the text refers back to it later. Otherwise, use unnumbered environments (`equation*`, `align*`).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Linter Logic**: Collect all labeled equations `\label{eq:foo}`. Check if `eq:foo` is referenced with `\eqref{eq:foo}` or `\ref{eq:foo}`. Flag unreferenced numbered equations.

### MATH-03: Equation Referencing Syntax

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Reference numbered equations using `\eqref{...}`. Omit the word "equation" in running text (e.g. "as shown in (2.4)"), except at the beginning of a sentence ("Equation (2.4) describes...").
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Regex Pattern**: `(?i)\b(equation|eq\.)\s*~?\\eqref\{` or `(?i)\b(Gleichung|Gl\.)\s*~?\\eqref\{` (except when capitalized at sentence start).

### MATH-04: Forbid Inline `\frac`

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Never use `\frac` in inline math (`$...$`). Reserve `\frac` for displayed equations. In inline math, use a slash (e.g. `$a/b$`) or negative exponent (`$s^{-1}$`).
- **Source**: `AGENTS.md` (Equations).
- **Regex Pattern**: `(?<!\\begin\{[^}]*\})[^\$\n]*\$[^\$\n]*\\frac\{`
- **Review Criteria**: Flag all instances of `\frac` inside inline math environments.

### MATH-05: Complete Relations over Bare Expressions

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: A displayed formula must be a complete relation with an operator ($=$, $\le$, $\approx$), never a bare expression (write $v(t) = gt$, not just $gt$).
- **Source**: `AGENTS.md` (Equations).
- **Review Criteria**: Inspect displayed equations to verify they state a complete equation, definition, or inequality.

### MATH-06: Thin Space for Formula Variables and Units

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Separate product variables within a formula with `\,` where juxtaposition is ambiguous. Separate physical values from their units with `\,` (or use `\si{...}` / `\unit{...}` from `siunitx`).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Regex Pattern**: Flag numbers glued directly to units: `\b\d+\s*(kg|m|s|V|A|Hz|rad|dB)\b` without `\,` or `\si{...}` / `\unit{...}`.

### MATH-07: Typography of Mathematical Variables and Matrices

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**:
  - Scalars: italic lowercase ($x, y$).
  - Vectors: bold upright lowercase ($\mathbf{x}$, `\ve{x}`).
  - Matrices: bold upright uppercase ($\mathbf{A}$, `\mat{A}`).
  - Greek letters: lowercase italic ($\alpha, \beta$), uppercase upright ($\Gamma, \Phi$).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex* (sec:Mathematische Formeln).
- **Review Criteria**: Verify consistent semantic formatting of vectors, matrices, and scalars.

### MATH-08: Index Typography (Counting vs Label vs Number)

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**:
  - Running index (counts): italic (e.g. $x_i, a_{jk}$).
  - Words, abbreviations, or constant labels: upright text (e.g. $U_\mathrm{rms}$, $K_\mathrm{crit}$).
  - Numbers: upright, never italic (e.g. $x_1$, not italic $1$).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Regex Pattern**: Subscripts containing multi-letter words without `\mathrm`: `_[a-zA-Z]{2,}(?![a-zA-Z]*\})`

### MATH-09: Separate Code and Math Notation

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Keep programming language syntax and mathematical notation separate. Write $A^{-1}b$ in math, not Matlab syntax $A\backslash b$.
- **Source**: `AGENTS.md` (Equations).
- **Regex Pattern**: `\$[^$]*(\.\*|\.\^|\\)[^$]*\$`
- **Review Criteria**: Flag programming language operators leaking into math environments.

### MATH-10: Introduce Every Variable in Surrounding Text

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Introduce and define every variable and symbol (including individual elements of a vector) in the text immediately before or after the equation where it first appears.
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Review Criteria**: For every variable in a formula, verify its definition exists within one paragraph of the equation.

### MATH-11: Prevent Awkward Formula Linebreaks

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Prevent inline formulas from breaking across lines awkwardly. Use `\linebreak` or enclose critical formulas in `\mbox{$...$}`.
- **Source**: `AGENTS.md` (Equations).
- **Review Criteria**: Scan compiled output logs for bad breaks in formulas.

### MATH-12: Upright Standard Operators, Functions, and Constants

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Set standard mathematical functions ($\sin, \cos, \log, \exp, \max$), differential operators ($\mathrm{d}t$), imaginary unit ($\mathrm{j}$ or $\mathrm{i}$), and Euler's constant ($\mathrm{e}$) upright.
- **Source**: IAT *Hinweise_Allgemein.tex* (DIN 1338).
- **Regex Pattern**: Look for `d x` or `d t` instead of `\ud t` or `\mathrm{d}t`: `\$\s*[^$]*\bdt\b[^$]*\$` or `sin\(` instead of `\sin(`.

### MATH-13: Forbid Blank Lines Inside Math Environments

- **Layer**: `[Regex Linter]`
- **Rule**: Do not place empty lines inside math environments (`align`, `equation`). To visually format source code, use comment lines containing only `%`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Gliederung, Mathematische Formeln).
- **Regex Pattern**: `\\begin\{(equation|align|gather)\*?\}(?:(?!\\end).)*\n\s*\n(?:(?!\\end).)*\\end` (dotall mode).

### MATH-14: Decimal Separator Consistency

- **Layer**: `[Regex Linter]`
- **Rule**: In English documents, use a decimal point ($2.5$). In German documents, use a decimal comma ($2{,}5$) wrapped in braces or managed by `icomma`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen).
- **Regex Pattern**: In English documents, flag numbers with commas: `\$\s*\d+,\d+\s*\$`.

---

## 5. Figures and Visuals

### FIG-01: Python Figure Generation Colocation

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: Every generated figure must have its generating Python script stored in the same directory, sharing the figure's base name (e.g. `figures/03_foundations/excitability_regimes.py` generates `excitability_regimes.pdf`). Run figures with `uv run`.
- **Source**: `AGENTS.md` (Figures).
- **Linter Check**: For every `\includegraphics{.../name.pdf}`, verify `.../name.py` exists on disk.

### FIG-02: Mandatory Background Grid

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Every plot and graph figure must display a background grid to aid data interpretation.
- **Source**: `AGENTS.md` (Figures).
- **Review Criteria**: Inspect generated plot figures and scripts to verify `ax.grid(True)` or `pgfplots` grid is enabled.

### FIG-03: Floating Figures and Text Referencing

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: All figures must float in a `figure` environment, must have a unique `\label{fig:...}`, and must be explicitly referenced in the body text using `\ref{fig:...}`.
- **Source**: `AGENTS.md` (Figures); IAT *Hinweise_Allgemein.tex*, *Anhang.tex*.
- **Linter Check**: Collect all `\label{fig:...}`. Ensure each is referenced with `\ref{fig:...}` or `\autoref{fig:...}`. Ensure no figures are embedded without `figure` environments.

### FIG-04: Axis Labels with Physical Units (DIN 461)

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Label every plot axis with the quantity name or symbol and its physical unit (e.g. $t$ in `\si{s}`, or $v$ / `\si{m/s}`).
- **Source**: `AGENTS.md` (Figures); IAT *Hinweise_Allgemein.tex* (DIN 461).
- **Review Criteria**: Inspect all plot axes to confirm both physical quantity and unit are clearly stated.

### FIG-05: Multi-Curve Legends

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Every plot showing more than one curve must include a legend or direct in-plot curve labels.
- **Source**: `AGENTS.md` (Figures).
- **Review Criteria**: Check plots containing multiple lines for unambiguous legends or text labels.

### FIG-06: Self-Contained Long Captions Ending in a Full Stop

- **Layer**: `[Regex Linter]` `[Review Agent]`
- **Rule**: Every figure must carry a comprehensive caption describing what the figure shows so the figure is understandable on its own without reading the main text. The caption must end with a full stop.
- **Source**: `AGENTS.md` (Figures); IAT *Tipps.tex*, *Anhang.tex*.
- **Regex Pattern**: `\\caption\{(?![^{}]*\\caption)[^}]*[^.!?]\}`
- **Review Criteria**: Ensure the caption explains curves, abbreviations, and experimental conditions shown.

### FIG-07: Caption Placement Below Figure

- **Layer**: `[Regex Linter]`
- **Rule**: In `figure` environments, `\caption{...}` must be placed below the image (`\includegraphics` or `tikzpicture`), followed by `\label{fig:...}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Gleitobjekte).
- **Regex Pattern**: In a `figure` environment, flag `\caption` occurring before `\includegraphics` or `\input{...tikz}`.

### FIG-08: Centering of Figures

- **Layer**: `[Regex Linter]`
- **Rule**: Center every figure using `\centering` inside the `figure` environment. Do not use the `\begin{center}` environment inside floats because it adds unwanted vertical whitespace.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Bilder).
- **Regex Pattern**: `\\begin\{figure\}(?:(?!\\end\{figure\}).)*\\begin\{center\}`

### FIG-09: Vector Format Preference and Font Consistency

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Prefer vector graphics (PDF, TikZ, pgfplots). Ensure fonts and font sizes within vector plots match the surrounding document typography.
- **Source**: IAT *Hinweise_Allgemein.tex*, *Anhang.tex* (cha:Anhang-Grafiken).
- **Review Criteria**: Verify diagrams and plots are rendered as vector PDFs, with text rendered in document fonts.

### FIG-10: Black-and-White Print Legibility

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Graphics must remain legible when printed in grayscale. Pure RGB green `(0, 1, 0)` is forbidden. Differentiate curves using line patterns (solid, dashed, dotted) or markers in addition to color.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Bilder), *Anhang.tex*.
- **Review Criteria**: Inspect plot scripts for line styles, markers, and color palettes that survive monochrome conversion.

---

## 6. Tables and Code Snippets

### TAB-01: Professional Horizontal Rules (Booktabs Principle)

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Format tables following `booktabs`. Never use vertical lines (`|`). Use only horizontal rules: `\toprule`, `\midrule`, `\bottomrule`, and `\cmidrule`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Tabellen).
- **Regex Pattern**: `\\begin\{tabular\}\{[^}]*\|[^}]*\}`
- **Review Criteria**: Reject any table with vertical bars in column specifications.

### TAB-02: Caption Placement Above Table

- **Layer**: `[Regex Linter]`
- **Rule**: In `table` environments, `\caption{...}` must be placed above the `tabular` environment, followed by `\label{tab:...}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Gleitobjekte, Tabellen), *Anhang.tex*.
- **Regex Pattern**: In a `table` environment, flag `\caption` occurring after `\end{tabular}`.

### TAB-03: Centering of Tables

- **Layer**: `[Regex Linter]`
- **Rule**: Center every table float using `\centering`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Tabellen).
- **Regex Pattern**: `\\begin\{table\}(?:(?!\\centering|\\end\{table\}).)*\\begin\{tabular\}`

### TAB-04: Explicit Units in Table Columns

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Every physical quantity in a table must include its unit in the column header or in a dedicated unit column (e.g. "$m$ in `\unit{kg}`").
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Tabellen).
- **Review Criteria**: Check table headers for unambiguous physical units.

### CODE-01: Monospace Font for Code

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: All source code, terminal commands, function names, and file paths must be set in monospace (`\texttt{...}` or `\verb|...|`, or `listings` environments).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Einbinden von Quellcode).
- **Review Criteria**: Flag unformatted code or variable names in body text.

### CODE-02: Restrict Code Snippets in Main Body

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Include only short, illustrative code fragments in the main text. Move full scripts or implementations to the appendix or separate project archive.
- **Source**: IAT *Hinweise_Allgemein.tex*, *Tipps.tex*.
- **Review Criteria**: Flag listings in main body exceeding 25 lines.

### CODE-03: Code Commented in English

- **Layer**: `[Review Agent]`
- **Rule**: All project code and script listings must be clearly commented in English.
- **Source**: IAT *Tipps.tex* (sec:Ergebnissicherung).
- **Review Criteria**: Verify comments in code listings and accompanying Python scripts are written in English.

---

## 7. Typography, Punctuation, and LaTeX Mechanics

### TYPO-01: Non-Breaking Spaces Before References and Citations

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Always use a non-breaking space `~` before `\ref{...}`, `\eqref{...}`, `\pageref{...}`, and `\cite{...}` to prevent orphaned numbers across line breaks.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Gleitobjekte, Sonderzeichen); `AGENTS.md`.
- **Regex Pattern**: `(?<!~)\\(ref|eqref|pageref|cite)\{` (check preceded by whitespace rather than `~`).

### TYPO-02: Non-Breaking Spaces in Fixed Expressions

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Use a non-breaking space `~` in fixed multi-word entities: titles with names (`Dr.~Müller`), times (`3~Uhr` / `3~p.m.`), and values with units where not wrapped in `\si` / `\unit` (`10~V`).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen).
- **Regex Pattern**: `\b(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+(?!~)[A-Z]`

### TYPO-03: Thin Spaces in Abbreviations and Number-Unit Pairs

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Use a thin space `\,` between components of abbreviated phrases (in German: `z.\,B.\`, `d.\,h.\`, `u.\,a.\`; in English: `e.\,g.\,`, `i.\,e.\,`).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen).
- **Regex Pattern**: `\b(z\.\s*B\.|d\.\s*h\.|u\.\s*a\.|e\.\s*g\.|i\.\s*e\.)\b` lacking `\,`.

### TYPO-04: Escaped Spaces After Parameterless LaTeX Commands

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Parameterless LaTeX macros swallow following whitespace. Terminate them with `\` or `{}` in running text (e.g. `\LaTeX\ is...` or `\LaTeX{} is...`).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen).
- **Regex Pattern**: `\\(LaTeX|TeX|BibTeX)\s+[a-zA-Z]` (macro not followed by `\`, `{}`, or punctuation).

### TYPO-05: Typographical Dash Distinctions

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**:
  - Hyphen (`-`): Compound words (`closed-loop`), no space.
  - En-dash (`--`): Number ranges (`153--165`), no space. In German prose, Gedankenstrich with spaces (`Wort -- Wort`).
  - Em-dash (`---`): Disfavored by `unslop`; if used in English, no surrounding spaces.
  - Minus sign (`$-$`): Always use math mode for negative numbers (`$-5$`, never text hyphen `-5`).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen); `unslop`.
- **Regex Pattern**:
  - Text hyphen for negative numbers: `(?<=\s)-(?=\d+)`
  - Text hyphen for numeric ranges: `\b\d+\s*-\s*\d+\b` instead of `--`.

### TYPO-06: Language-Specific Quotation Marks

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Never use straight typewriter quotes (`"quote"`). In English, use ``` ``quote'' ```. In German, use `"`quote`"'` or `\glqq quote\grqq{}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Sonderzeichen).
- **Regex Pattern**: `(?<!\\verb[|!])"[a-zA-Z0-9]` or `[a-zA-Z0-9]"(?!>)`

### TYPO-07: Single Attribute Emphasis Rule

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Change only one font attribute for emphasis (prefer `\emph{...}`). Never combine bold, italics, and underlining. Underlining (`\underline`) and letter-spacing (`sperren`) are strictly forbidden.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Auszeichnungen und Hervorhebungen).
- **Regex Pattern**: `\\underline\{` or `\\textbf\{[^}]*\\textit` or `\\textit\{[^}]*\\textbf`

### TYPO-08: Forbid `\\` for Paragraph Breaks in Body Text

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Never use `\\` or `\newline` to create paragraph breaks in running text. Create paragraphs using blank lines in the source. Reserve `\\` for table rows and multiline equations.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Gliederung).
- **Regex Pattern**: `(?<!\\\\)\\\\\s*$` in running text outside `tabular`, `align`, `array`, `matrix`.

### TYPO-09: Standard Label Prefixes

- **Layer**: `[Regex Linter]` `[Writing Skill]`
- **Rule**: Every `\label` must start with its standard category prefix:
  - `cha:` for chapters
  - `sec:` for sections and subsections
  - `fig:` for figures
  - `tab:` for tables
  - `eq:` for equations
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Gleitobjekte).
- **Regex Pattern**: `\\label\{(?!cha:|sec:|fig:|tab:|eq:)[^}]+\}`

### TYPO-10: Explicit Reference Categorization

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Always specify the object type before a reference ("Figure~4.2", "Section~3.1", "Chapter~2"). Never write bare numbers like "see 4.2", except for equations referenced as `(4.2)` or `\eqref{...}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Gleitobjekte).
- **Review Criteria**: Check that all `\ref{...}` calls are preceded by a descriptive category noun.

### TYPO-11: Chronological Referencing (No Forward References to Math)

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Introduce equations before or at the point of reference. Avoid referring forward to equations that have not yet appeared in the text.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Mathematische Formeln).
- **Review Criteria**: Ensure equation references refer back to previously stated formulas.

### TYPO-12: Acronym and Symbol Table Maintenance

- **Layer**: `[Review Agent]` `[Writing Skill]`
- **Rule**: Manage abbreviations using the `acro` package (or `glossaries`). Define acronyms on first use, abbreviate thereafter. Synchronize and update the symbols and acronyms table for every new notation added.
- **Source**: `AGENTS.md` (Equations); IAT *Tipps.tex*.
- **Review Criteria**: Verify all acronyms appearing in the text are defined in the acronyms list.

---

## 8. Workflow, Verification, and Submission Checklist

### WORK-01: Standard TeX Compilation Pipeline

- **Layer**: `[Regex Linter]`
- **Rule**: Compile the document using the standard engine sequence:

  ```bash
  pdflatex -> biber -> pdflatex -> pdflatex
  ```

  targeting the `out/` build directory, or use `latexmk -pdf -outdir=out`.
- **Source**: `AGENTS.md` (Latex); IAT *Hinweise_LaTeX.tex*.
- **Review Criteria**: Verify build scripts or Makefiles follow this multi-pass sequence.

### WORK-02: Zero LaTeX Warnings and Errors

- **Layer**: `[Regex Linter]`
- **Rule**: Compilation log must be clean. Resolve all `LaTeX Warning: There were undefined references`, `multiply defined labels`, and float placement warnings.
- **Source**: IAT *Anhang.tex* (Checkliste).
- **Review Criteria**: Parse `.log` file during build. Fail if undefined citations, broken references, or unresolved labels exist.

### WORK-03: Two-Sided Layout and Document Options

- **Layer**: `[Regex Linter]`
- **Rule**: Final document must be set up for two-sided printing (`twoside` enabled, DIN A4: 210 mm x 297 mm). The options `draft`, `oneside`, and `nohyperref` must NOT be active in the final build.
- **Source**: IAT *Anhang.tex* (Checkliste).
- **Regex Pattern**: `\\documentclass\[[^\]]*(draft|oneside|nohyperref)[^\]]*\]`

### WORK-04: PDF/A Compliance and Metadata Verification

- **Layer**: `[Review Agent]`
- **Rule**: The generated PDF must be a valid PDF/A document for submission to TUbama. Document properties (title, author, subject) must be populated via `\hypersetup{...}`.
- **Source**: IAT *Anhang.tex* (Checkliste).
- **Review Criteria**: Check PDF document properties and verify PDF/A conformance.

### WORK-05: Git Version Control and External Backup

- **Layer**: `[Review Agent]`
- **Rule**: Version all thesis files and code in Git from project start. Back up regularly to remote university storage (Hessenbox).
- **Source**: IAT *Tipps.tex* (Phase 2).
- **Review Criteria**: Verify `.git` tracking and clean directory hygiene.

### WORK-06: Oral Defense Preparation Standards

- **Layer**: `[Writing Skill]`
- **Rule**:
  - Defense talk duration: 20 minutes (hard cutoff at 25 minutes).
  - Reduce thesis to approximately 10 core slides (1-2 minutes per slide).
  - Slide design: bullet points only (no full sentences), emphasize diagrams over text.
  - Practice presentations and conduct a mandatory rehearsal with the supervisor.
- **Source**: IAT *Tipps.tex* (sec:Verteidigung), *Beurteilung.tex*.
