---
name: thesis-writing
description: Guidelines and restrictions for writing.
disable-model-invocation: true
---

# Thesis writing

When drafting or editing thesis text, adhere to the following rules and restrictions. After drafting, run `uv run latex-lint check <root-file>.tex` to verify mechanical formatting constraints.

## Structure

### STRUC-05: Mandatory section transitions

Bridge every section into the next with an explicit transition sentence or paragraph in the opening. The reader must understand why each section follows the preceding one.

### STRUC-07: Conclusion scope and outlook

State no new results, data, or methods in the conclusion. Restrict the conclusion strictly to summarizing key findings, synthesizing insights, and outlining future work.

## Prose and style

### PROSE-01: Concise and active prose (POEM principle)

Write according to POEM: Prägnanz (conciseness), Ordnung (logical order), Einfachheit (simplicity), Motivation (purpose). Clarity beats stylistic ornamentation. Split sentences exceeding 35 words or containing multiple nested clauses.

### PROSE-05: Consistent terminology

Always use the identical technical term for the same concept, variable, or component throughout the entire thesis. Do not cycle synonyms (such as alternating between "setpoint", "reference signal", and "command variable") for literary variety.

### PROSE-08: Eliminate AI tells and slop

Follow the `/unslop` skill across all prose. Remove promotional rhetoric ("pivotal", "delve", "crucial", "testament"), generic chatbot transitions, and robotic boilerplate. Prefer plain, concrete verbs and direct active voice.

## Claims and citations

### CITE-01: Universal substantiation of claims

Back every technical claim, empirical premise, or numerical parameter choice with a citation, formal proof, or experimental data. Standard mathematical steps need only a recognized keyword (such as "follows by integration by parts"). Paraphrase sources rather than using direct quotations.

### CITE-05: Common knowledge boundary

Apply the MIT common knowledge test: would a peer in your field at your academic stage know this fact without looking it up? Foundational facts (basic calculus, Ohm's law) need no citation. Specialized theorems, empirical lookup tables, and controller tuning formulas require explicit citations.

## Mathematics and notation

### MATH-05: Complete relations over bare expressions

State every displayed formula as a complete relation with an operator ($=$, $\le$, $\approx$), never as a bare floating expression (write $v(t) = gt$, not just $gt$).

### MATH-07: Typography of mathematical variables and matrices

Format symbols according to their mathematical category:

- Scalars: italic lowercase ($x, y$).
- Vectors: bold upright lowercase ($\mathbf{x}$ or semantic macro `\ve{x}`).
- Matrices: bold upright uppercase ($\mathbf{A}$ or semantic macro `\mat{A}`).
- Greek letters: lowercase italic ($\alpha, \beta$), uppercase upright ($\Gamma, \Phi$).

### MATH-08: Index typography (counting vs label vs number)

Format indices according to their specific purpose:

- Running indices (counting elements): italic (e.g. $x_i, a_{jk}$).
- Words, abbreviations, or constant labels: upright text via `\mathrm{...}` or `\text{...}` (e.g. $U_\mathrm{rms}$, $K_\mathrm{crit}$).
- Numeric indices: upright numbers, never italic (e.g. $x_1$, not italic $1$).

### MATH-10: Introduce every variable in surrounding text

Define every variable, parameter, and vector element in the text immediately before or after the formula where it first appears. Never leave symbols undefined for the reader to infer.

### MATH-11: Prevent awkward formula linebreaks

Keep inline mathematical formulas intact across line breaks. Use `\linebreak` hints or enclose unbreakable expressions in `\mbox{$...$}` to prevent operators or symbols from orphan splitting across lines.

## Figures and visualization

### FIG-02: Mandatory background grid

Include a visible background grid on every plot and coordinate graph figure to aid quantitative interpretation (`ax.grid(True)` in Python scripts or `grid=both` in pgfplots).

### FIG-04: Axis labels with physical units (DIN 461)

Label every plot axis with the quantity name or symbol and its physical unit formatted per DIN 461 (e.g. "$v$ in m/s" or "$v / (\si{m/s})$"). Never leave bare numbers on an axis without units.

### FIG-05: Multi-curve legends

Provide an explicit legend or direct on-curve text labels on every plot that displays more than one curve.

### FIG-09: Vector format preference and font consistency

Render all plots and diagrams as vector graphics (PDF, TikZ, or pgfplots). Ensure that fonts, font sizes, and weight in generated vector figures match the typography of the surrounding LaTeX document.

## Terminology and abbreviations

### TYPO-12: Acronym and symbol table maintenance

Manage abbreviations using the `acro` package. Spell out acronyms on first usage, abbreviate thereafter. Update the thesis symbol and acronym tables whenever introducing new notation or abbreviations.
