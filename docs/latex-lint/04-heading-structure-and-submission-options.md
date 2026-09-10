# 04 - Heading structure and submission options

**What to build:** An author can find overly deep numbered headings, parents with only one subheading, and explicit document-class options forbidden for final submission.

**Blocked by:** 03 - Check a thesis across included files.

## Acceptance criteria

- [ ] STRUC-02 checks excessive numbered heading depth against the prescribed chapter, section, and subsection hierarchy. Document the handling of starred headings and explicit numbering controls.
- [ ] STRUC-03 reports a parent with exactly one numbered child at the relevant level. A second child satisfies the rule even when it appears in another included source.
- [ ] Hierarchy checks use document order and do not confuse adjacent branches, comments, or command arguments with sibling headings.
- [ ] WORK-03 detects explicitly forbidden document-class options, including draft, oneside, and nohyperref, as options rather than arbitrary substrings.
- [ ] WORK-03 states that it does not establish class defaults, effective page dimensions, or complete submission compliance.
- [ ] All three rules are enabled by default, use the shared catalogue, support existing suppressions, and produce equivalent API and CLI findings.
- [ ] Each rule has focused unit tests for violations, valid counterparts, and relevant boundaries such as optional arguments, starred headings, and multiline declarations.
- [ ] An integration fixture covers hierarchy across includes and verifies actionable diagnostic locations. A same-line suppression test establishes where an isolated-subheading finding is attached.
- [ ] Each rule has passing and failing examples and documented coverage in CLI and library rule help.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
