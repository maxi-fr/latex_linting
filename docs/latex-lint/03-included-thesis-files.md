# 03 - Check a thesis across included files

**What to build:** An author can check a thesis from its root document and receive correctly located findings from literal input and include targets, with failures for missing source files and file-local suppression behavior.

**Blocked by:** 02 - Rule suppressions.

## Acceptance criteria

- [ ] The API and CLI recursively follow literal input and include commands from the explicitly supplied root.
- [ ] Source traversal preserves inclusion order so later document-wide rules can evaluate headings and structure in reading order.
- [ ] Literal relative-path resolution and omitted-extension handling are documented and covered by nested-file fixtures. Dynamic targets constructed by macros remain unsupported.
- [ ] Include-like text inside comments or literal code does not load additional files.
- [ ] Findings from included sources retain their original filenames, one-based positions, and excerpts. Repeated runs give the same ordering.
- [ ] A missing included file produces a useful failure identifying the include location and unresolved target. The CLI cannot report a successful complete check.
- [ ] A parent's disabled rules do not carry into included files. A child's directives do not alter the parent's state. Returning to the parent restores that file's own state.
- [ ] Invocation-wide exclusions affect all loaded sources, and unknown source-directive IDs are validated in included files.
- [ ] Public API fixtures exercise a root with multiple and nested includes, violations in different files, correct positions, missing targets, and suppression isolation.
- [ ] A CLI integration test checks a small multi-file thesis and verifies the same findings as the API. All existing MATH-04 unit tests remain green.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
