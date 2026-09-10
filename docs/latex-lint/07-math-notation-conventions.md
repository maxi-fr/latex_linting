# 07 - Math notation conventions

**What to build:** An author receives bounded source checks for number-unit spacing, programming operators in mathematics, upright standard function notation, and suspected decimal commas in English math.

**Blocked by:** 06 - Displayed math and section endings.

## Acceptance criteria

- [ ] MATH-06 detects recognizable number-unit spacing violations and accepts the documented thin-space and unit-command alternatives. It does not infer physical meaning or ambiguous variable products.
- [ ] MATH-09 detects documented programming operators in math. Ordinary LaTeX command backslashes are valid and must not be flagged wholesale.
- [ ] MATH-12 detects recognized standard functions or operators that should use upright notation. It does not infer whether an arbitrary letter is a mathematical constant.
- [ ] MATH-14 detects documented decimal-comma patterns in English math and explains ambiguity where comma-separated quantities may resemble decimals.
- [ ] All four checks respect inline and displayed math contexts, comments, literal code, and nested commands.
- [ ] All rules run by default, including bounded heuristics, and participate in the existing suppression mechanisms.
- [ ] Each rule has focused unit tests for violations, valid notation, documented ambiguous cases, relevant context boundaries, and source positions.
- [ ] Messages recommend concrete corrections and accurately describe detection limits. Each rule has passing and failing examples in CLI and library help.
- [ ] An API and CLI fixture demonstrates the new findings alongside existing math rules without changing established behavior.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
