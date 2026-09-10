# 12 - Dashes, quotation marks, emphasis, and paragraph breaks

**What to build:** An author can find incorrect numeric dash notation, straight prose quotation marks, forbidden emphasis commands, and line-break commands used as paragraph breaks.

**Blocked by:** 06 - Displayed math and section endings.

## Acceptance criteria

- [ ] TYPO-05 checks recognizable text negatives and numeric ranges using the wrong notation. Valid compound-word hyphens and math minus signs pass.
- [ ] TYPO-06 detects straight quotation marks in English prose while excluding literal code and escaped command syntax.
- [ ] TYPO-07 detects explicit forbidden emphasis commands and supported combinations of multiple font attributes, including nested commands.
- [ ] TYPO-08 detects explicit line-break commands used as paragraph breaks in running text and allows row breaks in supported tables and multiline math.
- [ ] Supported commands and environments are documented. Comments, nesting, math, and table context preserve the distinction between violations and valid source.
- [ ] All four rules run by default and use the existing suppression mechanisms.
- [ ] Every rule has focused unit tests for a violating example, valid alternatives, and relevant context, escaping, nesting, or multiline boundaries.
- [ ] Tests verify actionable positions and corrections, including for nested emphasis and prose following a table or math environment.
- [ ] API and CLI fixtures report consistent results, and each rule has accessible help with passing and failing examples and known limits.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
