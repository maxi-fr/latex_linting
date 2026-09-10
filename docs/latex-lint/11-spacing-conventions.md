# 11 - Spacing conventions

**What to build:** An author receives actionable findings for reference spacing, fixed-expression spacing, abbreviation spacing, and swallowed spaces after known parameterless commands.

**Blocked by:** 03 - Check a thesis across included files.

## Acceptance criteria

- [ ] TYPO-01 checks nonbreaking spaces before supported reference and citation commands where the prose calls for a preceding space. Document handling of optional arguments and commands at prose boundaries.
- [ ] TYPO-02 checks documented fixed expressions and recognizable number-unit forms that require nonbreaking spacing.
- [ ] TYPO-03 checks the prescribed thin spaces within supported English abbreviations. German language profiles are not introduced.
- [ ] TYPO-04 detects swallowed spaces after the documented set of parameterless commands and accepts supported explicit terminators.
- [ ] Checks exclude comments, literal code, and irrelevant command arguments. Existing proper nonbreaking spaces, thin spaces, and supported unit commands pass.
- [ ] All four rules run by default and support file-local and invocation-wide exclusions.
- [ ] Each rule has focused unit tests with violating and valid forms, punctuation boundaries, relevant optional arguments, multiline source, and source positions.
- [ ] Public API and CLI fixtures confirm consistent findings and targeted suppression when multiple spacing rules apply.
- [ ] Rule help documents each bounded expression or command set, correction, and passing and failing examples.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
