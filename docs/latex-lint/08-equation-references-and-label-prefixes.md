# 08 - Equation references and label prefixes

**What to build:** An author can find numbered equations without recognized references, incorrect equation-reference wording or commands, and nonstandard label prefixes across the thesis.

**Blocked by:** 06 - Displayed math and section endings.

## Acceptance criteria

- [ ] MATH-02 evaluates numbered equations against recognized references collected across the entire loaded document. A reference in another source file can satisfy the check.
- [ ] MATH-02 documents and tests how unlabeled numbered equations, unnumbered environments, and supported multiline numbering are treated.
- [ ] MATH-03 checks equation-reference syntax and redundant equation wording, preserving the allowed sentence-start exception.
- [ ] TYPO-09 checks standard chapter, section, figure, table, and equation label prefixes, using known context where available. It states what is checked when context is unknown.
- [ ] Label and reference commands in comments or literal code do not count. Nested source structure and optional arguments preserve locations.
- [ ] All three rules run by default, appear in the shared catalogue, and support source and invocation-wide suppressions.
- [ ] Each rule has focused unit tests for violations, valid counterparts, documented command forms, and relevant context or numbering exceptions.
- [ ] Document fixtures cover references before and after their targets and across includes. MATH-02 does not acquire an additional forward-reference prohibition.
- [ ] API and CLI findings agree on IDs and actionable locations. Tests establish suppression behavior for an unreferenced equation.
- [ ] Rule help includes passing and failing examples and makes the source-level coverage explicit.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
