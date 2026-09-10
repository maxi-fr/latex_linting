# Release Verification: Manual Installation and Integration Testing

## Overview

This document records the manual installation verification of `latex_linting` into an independent external project using `uv`, outside the library checkout. This satisfies Acceptance Criterion 4 of Ticket 13 (`docs/latex-lint/13-release-verification-and-usage-documentation.md`) and the Release Validation specification (`docs/latex-lint/spec.md`).

- **Tested Repository Revision / Base Commit:** `1c488730ef917ddf09cb01edabef6419829cf139` (Ticket 13 implementation state)
- **Environment:** Windows 11, CPython 3.13.2, `uv` package manager
- **Test Date:** 2026-09-10

---

## 1. External Project Initialization

A clean temporary project was created outside the checkout directory:

```bash
cd <temp_dir>/scratch/manual_verify
uv init --python 3.13
```

**Output:**

```text
Initialized project `manual-verify`
```

---

## 2. Dependency Installation via `uv add`

The `latex_linting` package was added as a local path dependency to the external project:

```bash
uv add "C:\Users\frank\latex_linting"
```

**Output:**

```text
Using CPython 3.13.2 interpreter at: C:\Users\frank\AppData\Local\Programs\Python\Python313\python.exe
Creating virtual environment at: .venv
Resolved 2 packages in 14ms
   Building latex-linting @ file:///C:/Users/frank/latex_linting
      Built latex-linting @ file:///C:/Users/frank/latex_linting
Prepared 1 package in 107ms
Installed 1 package in 71ms
 + latex-linting==0.1.0 (from file:///C:/Users/frank/latex_linting)
```

---

## 3. Test Fixture: Small Thesis

A sample LaTeX document `small_thesis.tex` was created in the external project root:

```latex
\documentclass{report}
\begin{document}
$\frac{1}{2}$
\end{document}
```

---

## 4. Python API Verification

A verification script `verify.py` imported `latex_linting.main` and invoked `check("small_thesis.tex")`:

```python
from latex_linting.main import Finding, check

findings = check("small_thesis.tex")
print(f"Findings count: {len(findings)}")
for f in findings:
    print(f"{f.filename}:{f.line}:{f.column}: {f.rule_id} {f.explanation}")
```

**Command:**

```bash
uv run python verify.py
```

**Output:**

```text
Findings count: 1
small_thesis.tex:3:2: MATH-04 Avoid \frac in inline math; reserve fractions for displayed equations.
```

**Exit code:** `0` (Python process completed successfully and returned expected structured `Finding` objects).

---

## 5. Console Command: `latex-lint check` (Unsuppressed Violation)

**Command:**

```bash
uv run latex-lint check small_thesis.tex
```

**Output (stdout):**

```text
small_thesis.tex:3:2: MATH-04 Avoid \frac in inline math; reserve fractions for displayed equations.
  $\frac{1}{2}$
  Suggestion: Use a slash such as $a/b$, a negative exponent such as $s^{-1}$, \sfrac from the xfrac package or move the fraction to display math.
```

**Exit code:** `1` (indicating unsuppressed findings detected, exactly matching spec).

---

## 6. Console Command: `latex-lint check --ignore` (Clean Check)

**Command:**

```bash
uv run latex-lint check --ignore MATH-04 small_thesis.tex
```

**Output:**
*(empty stdout, empty stderr)*

**Exit code:** `0` (clean run after invocation-wide exclusion).

---

## 7. Console Command: `latex-lint rule MATH-04` (Rule Help)

**Command:**

```bash
uv run latex-lint rule MATH-04
```

**Output (stdout):**

```text
MATH-04: Avoid \frac in inline math; reserve fractions for displayed equations.
Use a slash such as $a/b$, a negative exponent such as $s^{-1}$, \sfrac from the xfrac package or move the fraction to display math.

Passing examples:
$a/b$
$s^{-1}$
\[\frac{a}{b} \,.\]

Failing examples:
$\frac{a}{b}$
\(\frac{a}{b}\)

Detection limits:
Detects literal \frac commands in $...$, \(...\), and the math environment, including nested arguments and multiline input. Reports the command's backslash. Display delimiters are $$...$$ and \[...\]; display environments are displaymath, equation, align, alignat, gather, multline, flalign, eqnarray, and their starred forms except displaymath*. Comments, \verb, \verb*, verbatim, verbatim*, lstlisting, and minted are excluded. Environment names must be literal, with no comments inside the begin/end command. Does not expand macros, interpret text-mode command arguments, check \dfrac, \tfrac, or validate LaTeX syntax. Unclosed math continues to end of file; an unclosed literal environment consumes the rest of the file.
```

**Exit code:** `0` (rule help displayed successfully).

---

## Conclusion

All verification steps succeeded:

1. `uv` successfully installed `latex_linting` into an independent project.
2. The public API `from latex_linting.main import Finding, check` functioned as expected.
3. The console script `latex-lint` executed with correct formatting and exact exit codes (`0` for clean run and rule help, `1` for findings).
4. No external installation tests were added to the repository's automated test suite.
