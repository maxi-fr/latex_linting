# 06 - Displayed math and section endings

**What to build:** An author can identify missing display-math punctuation, forbidden blank math lines, colons before equations, and sections ending directly on a non-prose block.

**Blocked by:** 04 - Heading structure and submission options.

## Acceptance criteria

- [ ] MATH-01 checks terminal punctuation and the required thin spacing in supported displayed-math environments, including documented starred and multiline forms.
- [ ] MATH-13 detects genuinely blank lines in supported math environments while allowing comment-only lines.
- [ ] PROSE-07 reports a colon immediately before a supported displayed equation and does not claim to check the entire surrounding sentence's grammar.
- [ ] STRUC-06 reports a section ending directly on a recognized equation, list, table, or figure block before the next relevant heading or document end.
- [ ] Section endings use the actual heading hierarchy and inclusion order. A prose continuation in an included source can satisfy the rule.
- [ ] Nested environments, trailing labels, comments, and whitespace do not accidentally appear to be final prose or terminal math punctuation.
- [ ] Supported environments and treatment of multiline equations are documented. These source checks do not infer rendered layout or grammatical completeness.
- [ ] All four rules are enabled by default, support suppressions, and expose equivalent findings and rule help through the API and CLI.
- [ ] Every rule has focused unit tests with violating and valid examples, relevant nesting and multiline cases, and exact reported positions.
- [ ] Integration tests cover section boundaries across includes and suppressing a finding attached to a missing construct's relevant existing command.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
