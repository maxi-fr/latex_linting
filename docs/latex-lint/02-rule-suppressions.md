# 02 - Rule suppressions

**What to build:** An author can make deliberate exceptions through latex-lint comments or invocation-wide ignored rule IDs, while unexpected findings and misspelled IDs still fail the check.

**Blocked by:** 01 - First working lint check.

## Acceptance criteria

- [ ] Source directives use the latex-lint namespace followed by a colon, an ignore, disable, or enable action, an equals sign, and explicit comma-separated rule IDs.
- [ ] Ignore suppresses findings reported on its own source line only. It does not suppress the following line.
- [ ] Disable applies from the directive position until a corresponding enable or the end of that source file. Enable changes only the named rules.
- [ ] The CLI ignore option accepts comma-separated IDs, and the Python API accepts equivalent exclusions. Invocation-wide exclusions cannot be undone by an enable directive.
- [ ] Only actual LaTeX comments are interpreted as directives. Directive-like text inside literal code has no suppression effect.
- [ ] Unknown IDs in source comments, API arguments, or CLI arguments produce a useful error and cannot yield a successful CLI check.
- [ ] Validation uses the same catalogue as rule evaluation and help. Only implemented rule IDs are accepted; no placeholder rules are added for tests.
- [ ] Unit and API tests cover same-line boundaries, disable and enable behavior, end-of-file scope, unknown IDs, and invocation-wide precedence. Test multiple valid IDs as additional rules become available.
- [ ] The CLI demonstrates that a suppressed violation passes while an equivalent unsuppressed violation fails. User documentation explains syntax, reported-location semantics, and how to exclude German passages.
- [ ] No project configuration, wildcard rule selection, or automatic source edits are introduced.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
