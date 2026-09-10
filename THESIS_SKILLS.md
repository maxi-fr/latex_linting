# Thesis Skills Breakdown

This document categorizes thesis guidelines into two skills:

1. **Writing Skill**: Prescriptive guidelines for writing and generating text, math, figures, and tables.
2. **Reviewer Skill**: Inherits all Writing Skill points, plus audit and verification checks specific to review.

The sources are in docs/sources/

---

## 1. Writing Skill (Core Drafting Guidelines)

### STRUC-05: Mandatory Section Transitions

- **Rule**: Bridge every section into the next with a transition sentence or paragraph. A reader must never land in a new section without knowing why it follows the preceding one.
- **Source**: `AGENTS.md` (Structure).
- **Review Criteria**: Check the opening paragraph of each section for an explicit link to the previous section or overarching thesis goal.

### STRUC-07: Conclusion Scope and Outlook

- **Rule**: State no new results in the conclusion. The conclusion must only summarize key findings, synthesize insights, and provide an outlook on future work.
- **Source**: `AGENTS.md` (Structure); IAT *Zusammenfassung.tex*.
- **Review Criteria**: Verify that all statements and data in the conclusion refer back to previously discussed results.

### PROSE-01: Concise and Active Prose (POEM Principle)

- **Rule**: Write according to POEM: Prägnanz, Ordnung, Einfachheit, Motivation. Clarity beats stylistic ornamentation. Keep sentences focused; split multi-clause run-ons.
- **Source**: IAT *Tipps.tex*, *Hinweise_Allgemein.tex* (sec:Stilistische Punkte).
- **Review Criteria**: Flag sentences exceeding 35 words or containing deeply nested subordinate clauses.

### PROSE-05: Consistent Terminology (Ban Synonym Cycling)

- **Rule**: Always use the identical term for the same concept, variable, or component throughout the thesis. Do not vary technical names for literary variety.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Stilistische Punkte).
- **Review Criteria**: Check for alternating synonyms across chapters (e.g. interchanging "setpoint", "reference signal", "command variable").

### PROSE-08: Eliminate AI Tells and Slop

- **Rule**: Follow the `/unslop` skill. Remove AI language
- **Source**: `AGENTS.md` (Prose); `unslop` skill.
- **Review Criteria**: Search for banned AI vocabulary words, promotional tone, and robotic formulaic transitions.

### CITE-01: Universal Substantiation of Claims

- **Rule**: Back every assertion, premise, or parameter choice with a citation, proof, or experimental data. Standard textbook steps need only a recognized keyword ("follows by integration by parts").
- **Source**: `AGENTS.md` (Claims and citations); IAT *Hinweise_Allgemein.tex* (sec:Latex-Zitieren).
- **Review Criteria**: Flag unbacked empirical claims, unreferenced state-of-the-art assertions, or arbitrary numerical parameters.

### CITE-05: Common Knowledge Boundary

- **Rule**: Apply the MIT common knowledge test: would a fellow student at your academic stage know this fact without looking it up? Basic calculus and Ohm's law need no citation; specialized theorems, lookup tables, and controller tuning formulas require citations.
- **Source**: IAT *Hinweise_Allgemein.tex* (Grundwissen).
- **Review Criteria**: Ensure foundational material is not over-cited while specialized techniques are properly attributed.

### MATH-05: Complete Relations over Bare Expressions

- **Rule**: A displayed formula must be a complete relation with an operator ($=$, $\le$, $\approx$), never a bare expression (write $v(t) = gt$, not just $gt$).
- **Source**: `AGENTS.md` (Equations).
- **Review Criteria**: Inspect displayed equations to verify they state a complete equation, definition, or inequality.

### MATH-07: Typography of Mathematical Variables and Matrices

- **Rule**:
  - Scalars: italic lowercase ($x, y$).
  - Vectors: bold upright lowercase ($\mathbf{x}$, `\ve{x}`).
  - Matrices: bold upright uppercase ($\mathbf{A}$, `\mat{A}`).
  - Greek letters: lowercase italic ($\alpha, \beta$), uppercase upright ($\Gamma, \Phi$).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex* (sec:Mathematische Formeln).
- **Review Criteria**: Verify consistent semantic formatting of vectors, matrices, and scalars.

### MATH-10: Introduce Every Variable in Surrounding Text

- **Rule**: Introduce and define every variable and symbol (including individual elements of a vector) in the text immediately before or after the equation where it first appears.
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.
- **Review Criteria**: For every variable in a formula, verify its definition exists within one paragraph of the equation.

### MATH-11: Prevent Awkward Formula Linebreaks

- **Rule**: Prevent inline formulas from breaking across lines awkwardly. Use `\linebreak` or enclose critical formulas in `\mbox{$...$}`.
- **Source**: `AGENTS.md` (Equations).
- **Review Criteria**: Scan compiled output logs for bad breaks in formulas.

### FIG-02: Mandatory Background Grid

- **Rule**: Every plot and graph figure must display a background grid to aid data interpretation.
- **Source**: `AGENTS.md` (Figures).
- **Review Criteria**: Inspect generated plot figures and scripts to verify `ax.grid(True)` or `pgfplots` grid is enabled.

### FIG-04: Axis Labels with Physical Units (DIN 461)

- **Rule**: Label every plot axis with the quantity name or symbol and its physical unit (e.g. $v$ / `\si{m/s}`).
- **Source**: `AGENTS.md` (Figures); IAT *Hinweise_Allgemein.tex* (DIN 461).
- **Review Criteria**: Inspect all plot axes to confirm both physical quantity and unit are clearly stated.

### FIG-05: Multi-Curve Legends

- **Rule**: Every plot showing more than one curve must include a legend or direct in-plot curve labels.
- **Source**: `AGENTS.md` (Figures).
- **Review Criteria**: Check plots containing multiple lines for unambiguous legends or text labels.

### FIG-09: Vector Format Preference and Font Consistency

- **Rule**: Prefer vector graphics (PDF, TikZ, pgfplots). Ensure fonts and font sizes within vector plots match the surrounding document typography.
- **Source**: IAT *Hinweise_Allgemein.tex*, *Anhang.tex* (cha:Anhang-Grafiken).
- **Review Criteria**: Verify diagrams and plots are rendered as vector PDFs, with text rendered in document fonts.

### TYPO-12: Acronym and Symbol Table Maintenance

- **Rule**: Manage abbreviations using the `acro` package. Define acronyms on first use, abbreviate thereafter. Synchronize and update the symbols and acronyms table for every new notation added.
- **Source**: `AGENTS.md` (Equations); IAT *Tipps.tex*.
- **Review Criteria**: Verify all acronyms appearing in the text are defined in the acronyms list.

### MATH-08: Index Typography (Counting vs Label vs Number)

- **Rule**:
  - Running index (counts): italic (e.g. $x_i, a_{jk}$).
  - Words, abbreviations, or constant labels: upright text (e.g. $U_\mathrm{rms}$, $K_\mathrm{crit}$).
  - Numbers: upright, never italic (e.g. $x_1$, not italic $1$).
- **Source**: `AGENTS.md` (Equations); IAT *Hinweise_Allgemein.tex*.

---

## 2. Reviewer Skill (Extra Audit & Verification Points)

The reviewer skill evaluates all points from the **Writing Skill** above, plus the following 6 verification and audit points:

### STRUC-04: Narrative Problem-Solving Arc

- **Rule**: Tell the story of the problem and its solution rather than dumping an inventory of technical facts like a status report.
- **Source**: `AGENTS.md` (Structure); IAT *Tipps.tex*, *Beurteilung.tex*.
- **Review Criteria**: Ensure each chapter frames motivation, trade-offs, and conceptual steps rather than merely listing completed steps.

### PROSE-06: Negative Results Analysis

- **Rule**: When an approach fails or underperforms, provide a rigorous analysis explaining why the approach failed. Never sweep negative results under the rug.
- **Source**: IAT *Tipps.tex* (Inhalt und Umfang der Arbeit).
- **Review Criteria**: Ensure failed trials or rejected hypotheses include failure mechanisms, parametric limits, or root-cause explanations.

### CITE-07: In-Text Citation Precision

- **Rule**: When citing extensive works (books, monographs, long standards), provide specific page, chapter, or theorem numbers: `\cite[p.~123]{author2020}`.
- **Source**: IAT *Hinweise_Allgemein.tex* (Quellenverweise im Text).
- **Review Criteria**: Check that book citations provide page-level pinning for verification.

### CODE-01: Monospace Font for Code

- **Rule**: All source code, terminal commands, function names, and file paths must be set in monospace (`\texttt{...}` or `\verb|...|`, or `listings` environments).
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Einbinden von Quellcode).
- **Review Criteria**: Flag unformatted code or variable names in body text.

### TAB-04: Explicit Units in Table Columns

- **Rule**: Every physical quantity in a table must include its unit in the column header or in a dedicated unit column (e.g. "$m$ in `\unit{kg}`").
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Tabellen).
- **Review Criteria**: Check table headers for unambiguous physical units.

### FIG-10: Black-and-White Print Legibility

- **Rule**: Graphics must remain legible when printed in grayscale. Pure RGB green `(0, 1, 0)` is forbidden. Differentiate curves using line patterns (solid, dashed, dotted) or markers in addition to color.
- **Source**: IAT *Hinweise_Allgemein.tex* (sec:Latex-Bilder), *Anhang.tex*.
- **Review Criteria**: Inspect plot scripts for line styles, markers, and color palettes that survive monochrome conversion.
