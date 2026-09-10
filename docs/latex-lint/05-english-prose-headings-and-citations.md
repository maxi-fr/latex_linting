# 05 - English prose, headings, and citations

**What to build:** An author receives explained style findings for standalone demonstratives, suspected comma-before-that errors, heading capitalization, and citations placed after a terminal period.

**Blocked by:** 03 - Check a thesis across included files.

## Acceptance criteria

- [ ] PROSE-02 detects documented patterns for standalone This and These. A demonstrative followed by an explicit referent noun passes.
- [ ] PROSE-03 detects suspected comma-before-that violations in prose and describes grammatical uncertainty without claiming full parsing.
- [ ] PROSE-04 checks American headline capitalization in supported headings. Document the treatment of minor words, acronyms, hyphenated words, math, and nested commands.
- [ ] CITE-04 detects recognized citation commands after a sentence's terminal period and recommends moving the citation before it. Document supported citation forms and optional arguments.
- [ ] Checks apply to relevant English prose or heading content, excluding comments and literal code. Math and command syntax must not be treated as ordinary prose.
- [ ] All four rules run by default, including heuristics. Existing source and invocation suppressions allow exceptions and exclusions for German passages.
- [ ] Each rule has focused unit tests for a violation, a valid counterpart, documented exceptions, and applicable multiline or nested-argument cases.
- [ ] Tests verify heuristic wording, source positions, and corrections. Multiple-rule suppression tests demonstrate that ignoring one rule leaves the others active.
- [ ] A CLI fixture and equivalent API call report the new rules consistently. Each rule is available through rule help with examples and explicit detection limits.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
