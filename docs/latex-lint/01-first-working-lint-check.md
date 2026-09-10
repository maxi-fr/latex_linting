# 01 - First working lint check

**What to build:** An author can check one explicitly supplied LaTeX document through the Python API or the installed latex-lint command and receive an actionable MATH-04 finding for an inline fraction. This is the first complete path from source input to diagnostic and rule help.

**Blocked by:** None.

**Status:** Complete, 2026-09-10.

## Acceptance criteria

- [x] The existing package identity, Python requirement, and uv build approach are retained. The greeting placeholder is replaced where necessary to expose the linter; unrelated template cleanup is excluded.
- [x] The Python API checks a root document and returns structured findings without printing. The CLI check operation requires an explicit root document.
- [x] MATH-04 detects fractions in supported inline-math syntax and permits them in display math. Supported delimiters are documented.
- [x] Comments and supported literal-code constructs do not trigger the rule. Escaped comment characters, nested fraction arguments, and ordinary multiline input retain correct context and positions.
- [x] Each finding includes its rule ID, original filename, one-based line and column, source excerpt, concise explanation, and suggested correction.
- [x] The API and CLI agree on findings and return them deterministically. A clean check succeeds; findings and invalid input cause a nonzero CLI exit. Exit behavior is documented.
- [x] A shared rule catalogue exposes MATH-04 to evaluation and rule help. The CLI rule operation and library rule information include the explanation, passing and failing examples, and detection limits.
- [x] MATH-04 is enabled by default. Checking never edits the source and requires neither TeX compilation nor macro expansion.
- [x] Focused unit tests cover a violation, valid alternatives, context exclusions, nesting, multiline input, and source positions. CLI tests cover a clean check, a failing check, invalid input, and rule help.
- [x] Begin with failing behavior tests, run targeted checks while developing, and finish with the repository's full pre-commit gate. Keep changes within this ticket's scope.

## Implementation notes

- Added `latex_linting.main.check(root)`, `latex-lint check ROOT`, and `latex-lint rule MATH-04`.
- Separated source tracking, scanning, rule evaluation and help, orchestration, and CLI presentation. Tokens retain offsets into unchanged source text for later suppression and include handling.
- Each rule lives in its own module under `rules/`, starting with `math_04.py`. Shared rule metadata lives in `rules/model.py`, and `rules/catalogue.py` registers implemented rules for checking and help.
- MATH-04 checks literal `\frac` commands. Supported syntax, detection limits, source positions, exit codes, and the architecture are documented in [the README](../../README.md).
- Suppressions and included-file traversal remain in tickets 02 and 03.

## Validation

- Started with failing behavior tests before implementing the checker.
- All 59 tests passed, including tests of the installed CLI.
- Ruff checks, formatting checks, and type checks passed for the source and tests.
- `uv run pre-commit run --all-files` passed.
