---
name: thesis-review
description: Audit and verify LaTeX thesis drafts against academic writing standards and review criteria.
disable-model-invocation: true
---

# Thesis review

Review LaTeX thesis chapters, sections, or complete drafts against academic writing standards and verification criteria.

## Process

1. **Mechanical linting**: Run `uv run latex-lint check path/to/thesis.tex`. Resolve or record all mechanical issues first.
2. **Core drafting audit**: Check the text against the 11 core rules in [`thesis-writing`](../thesis-writing/SKILL.md).
3. **Specialized audit**: Check the text against the 10 extra review criteria below.
4. **Report findings**: List issues grouped by rule ID, citing exact file and line locations (`file.tex:line`), the offending excerpt, and the concrete fix.

## Extra review criteria

In addition to all core rules in [`thesis-writing`](../thesis-writing/SKILL.md), evaluate drafts against these 10 review-specific checks:

### PROSE-06: Negative results analysis

When an approach fails or underperforms, provide a rigorous analysis explaining failure mechanisms, parametric limits, or root causes.

### CITE-07: In-text citation precision

When citing extensive works (books, monographs, long standards), provide specific page, chapter, or theorem numbers (e.g. `\cite[p.~123]{author2020}`). Flag citations to extensive works lacking page-level pinning.

### TAB-04: Explicit units in table columns

Specify the measurement unit for every physical quantity in the table column header or in a dedicated unit column (e.g. "$m$ in `\unit{kg}`").

### STRUC-07: Conclusion scope and outlook

State no new results, data, or methods in the conclusion. Restrict the conclusion strictly to summarizing key findings, synthesizing insights, and outlining future work.

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

### FIG-02: Mandatory background grid

Include a visible background grid on every plot and coordinate graph figure to aid quantitative interpretation (`ax.grid(True)` in Python scripts or `grid=both` in pgfplots).

### FIG-04: Axis labels with physical units (DIN 461)

Label every plot axis with the quantity name or symbol and its physical unit formatted per DIN 461 (e.g. "$v$ in m/s" or "$v / (\si{m/s})$"). Never leave bare numbers on an axis without units.

### FIG-05: Multi-curve legends

Provide an explicit legend or direct on-curve text labels on every plot that displays more than one curve.

### FIG-09: Vector format preference and font consistency

Render all plots and diagrams as vector graphics (PDF, TikZ, or pgfplots). Ensure that fonts, font sizes, and weight in generated vector figures match the typography of the surrounding LaTeX document.
