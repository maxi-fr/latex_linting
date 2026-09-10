---
name: thesis-review
description: Audit and verify LaTeX thesis drafts against academic writing standards and review criteria.
disable-model-invocation: false
---

# Thesis review

Review LaTeX thesis chapters, sections, or complete drafts against academic writing standards and verification criteria.

## Process

1. **Mechanical linting**: Run `uv run latex-lint check path/to/thesis.tex`. Resolve or record all mechanical issues first.
2. **Core drafting audit**: Check the text against the 17 core rules in [`thesis-writing`](../thesis-writing/SKILL.md).
3. **Specialized audit**: Check the text against the 6 extra review criteria below.
4. **Report findings**: List issues grouped by rule ID, citing exact file and line locations (`file.tex:line`), the offending excerpt, and the concrete fix.

## Extra review criteria

In addition to all core rules in [`thesis-writing`](../thesis-writing/SKILL.md), evaluate drafts against these 6 review-specific checks:

### STRUC-04: Narrative problem-solving arc

- **Rule**: Tell the story of the problem and its solution rather than dumping an inventory of technical facts like a status report.
- **Review check**: Ensure each chapter and section frames motivation, trade-offs, and conceptual decisions rather than cataloging completed tasks.

### PROSE-06: Negative results analysis

- **Rule**: When an approach fails or underperforms, provide a rigorous analysis explaining why the approach failed. Never sweep negative results under the rug.
- **Review check**: Ensure failed experiments, rejected hypotheses, or suboptimal configurations discuss failure mechanisms, parametric limits, or root causes.

### CITE-07: In-text citation precision

- **Rule**: When citing extensive works (books, monographs, long standards), provide specific page, chapter, or theorem numbers: `\cite[p.~123]{author2020}`.
- **Review check**: Flag citations to books and extensive works that lack page-level or section-level pinning in the citation argument.

### CODE-01: Monospace font for code

- **Rule**: All source code, terminal commands, function names, and file paths must be set in monospace (`\texttt{...}` or `\verb|...|`, or `listings` environments).
- **Review check**: Flag unformatted code keywords, function names, CLI commands, or file paths appearing in regular text font.

### TAB-04: Explicit units in table columns

- **Rule**: Every physical quantity in a table must include its unit in the column header or in a dedicated unit column (e.g. "$m$ in `\unit{kg}`").
- **Review check**: Verify that table headers specify measurement units for all numerical columns presenting physical quantities.

### FIG-10: Black-and-white print legibility

- **Rule**: Graphics must remain legible when printed in grayscale. Pure RGB green `(0, 1, 0)` is forbidden. Differentiate curves using line patterns (solid, dashed, dotted) or markers in addition to color.
- **Review check**: Verify that plot curves differentiate by line styles or markers in addition to color, and that pure saturated green is not used.
