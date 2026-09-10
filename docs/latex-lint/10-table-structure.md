# 10 - Table structure

**What to build:** An author can find table column specifications that violate booktabs conventions, misplaced captions or labels, and missing table centering.

**Blocked by:** 06 - Displayed math and section endings.

## Acceptance criteria

- [ ] TAB-01 detects vertical rules in supported column specifications and recognized departures from the prescribed booktabs commands. Supported table forms are documented.
- [ ] TAB-01 distinguishes nested column arguments and repetition constructs from body content. It does not flag unrelated vertical-bar notation outside column specifications.
- [ ] TAB-02 checks that a table caption precedes the tabular content and that its label follows the caption.
- [ ] TAB-03 checks centering inside supported table floats.
- [ ] Comments, literal code, nested caption arguments, multiline declarations, and supported placement arguments retain correct context and positions.
- [ ] All three rules are enabled by default, participate in suppressions, and produce equivalent API and CLI findings.
- [ ] Each rule has focused unit tests for violations, valid booktabs tables, relevant nested syntax, and positions for missing or misplaced constructs.
- [ ] An integration fixture exercises multiple findings in one table and confirms that a targeted suppression leaves unrelated findings visible.
- [ ] Rule help provides passing and failing examples, supported forms, and partial-coverage limits. No semantic checks of column units or rendered layout are added.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
