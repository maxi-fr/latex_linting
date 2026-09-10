# 13 - Release verification and usage documentation

**What to build:** An author can install the finished library into another uv project and follow accurate documentation to check a thesis, interpret findings, inspect rule help, and suppress deliberate exceptions.

**Blocked by:** 01 through 12. Every preceding ticket must be complete.

## Acceptance criteria

- [ ] The implemented rule catalogue is reconciled with the specification. Every advertised rule is implemented, enabled by default, documented, and covered by focused unit tests.
- [ ] Partial checks and heuristics clearly state their boundaries. Deferred guidelines are not advertised as fully enforced.
- [ ] Usage documentation covers repository dependency installation through uv, the public API, the installed CLI, explicit root selection, rule help, suppressions, and failure behavior.
- [ ] A representative multi-file thesis fixture checks combined behavior for structure, prose, math, figures, tables, and typography. API and CLI results agree.
- [ ] Integration coverage includes a clean result, unsuppressed violations, source and invocation-wide exclusions, cross-file references, source positions, missing input, and unknown rule IDs.
- [ ] Multiple-rule tests verify comma-separated suppression lists and ensure targeted exclusions leave unrelated rules active.
- [ ] Manually create a separate temporary uv project and install this repository as a dependency. From outside the library checkout, import the public API, run the installed CLI on a small thesis, and inspect rule help.
- [ ] Record the manual installation result and the repository revision or working state tested. Installation into another project is not added to the automated suite.
- [ ] Run the appropriate targeted checks during implementation and the repository's complete pre-commit gate before declaring the release work complete.
- [ ] No automatic fixes, bibliography or asset checks, TeX compilation, configuration tables, editor integrations, or package-index publication are introduced.
