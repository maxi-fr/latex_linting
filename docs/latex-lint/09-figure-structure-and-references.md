# 09 - Figure structure and references

**What to build:** An author can check figure environments, labels, references, captions, ordering, and centering using the thesis sources alone.

**Blocked by:** 08 - Equation references and label prefixes.

## Acceptance criteria

- [ ] FIG-03 detects recognized figure content outside a figure environment, missing or duplicate figure labels, and figures without a recognized document reference.
- [ ] References collected from other included sources can satisfy FIG-03. References in comments and literal code cannot.
- [ ] FIG-06 checks caption presence and a terminal full stop. It does not claim to judge whether the caption is comprehensive or understandable.
- [ ] FIG-07 checks image, caption, and label ordering for supported figure contents. Document treatment of graphics, TikZ, and literal included figure content.
- [ ] FIG-08 checks centering and rejects a center environment inside a figure float.
- [ ] Supported starred floats, placement arguments, nested caption commands, and multiline figures are handled consistently and documented.
- [ ] All four rules are enabled by default, use existing suppressions, and provide original-source positions, excerpts, and suggested corrections.
- [ ] Every rule has focused unit tests for violating and valid figures plus relevant nesting, optional-argument, and source-context cases.
- [ ] API and CLI fixtures cover a figure referenced across included files, duplicate labels, and suppressing findings for missing captions or labels.
- [ ] Each rule exposes help with examples and detection limits. No asset existence, generating-script, plot-appearance, or rendered-output checks are added.
- [ ] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.
