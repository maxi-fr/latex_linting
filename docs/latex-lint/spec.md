# LaTeX thesis linter specification

## Problem Statement

The IAT thesis guidelines combine mechanical LaTeX conventions, writing advice, and requirements that need human judgment. Checking the mechanical conventions by hand is repetitive, and a list of suggested regular expressions does not provide a usable linter.

The author needs a Python dependency that another thesis project can install through uv. It should report actionable findings with stable rule IDs, like Ruff and markdownlint, and allow deliberate exceptions without editing the library.

The repository currently contains a Python package skeleton, a greeting function, and basic pytest tests. It has no linting engine or command-line interface. The existing package uses the uv build backend and requires Python 3.13 or later. There is no existing domain glossary or ADR governing this feature.

## Solution

Build a source linter specifically for the author's English IAT thesis. Provide an importable Python API and a command-line interface named `latex-lint`. Both use the same rule implementations and return equivalent findings.

The user supplies the root LaTeX document. The linter follows literal input and include commands, checks the resulting document, and reports findings against the original source files. Rules use regex matching with a small scanner that understands enough LaTeX context to distinguish prose, math, comments, code, command arguments, and environments.

Every implemented rule is enabled by default, including documented heuristics. Users can suppress specific rules on one line, within part of a file, or for an entire invocation. Every unsuppressed finding makes the CLI check fail. The first release reports corrections without modifying thesis files.

A useful finding tells the author where the problem is, which convention it concerns, and what to change. Rule help provides the longer explanation and examples.

## Implementation Decisions

### Interfaces and responsibilities

- Retain the existing Python package identity and uv packaging approach. Another project must be able to install this repository as a dependency and use both its API and console command. A package-index publication is not required.
- Expose a Python operation that checks a root document and accepts a collection of ignored rule IDs. Return structured findings rather than printing terminal output from the library.
- Provide a CLI `check` operation with an explicit root document argument and an `--ignore` option accepting comma-separated rule IDs. Do not infer a root from the current directory.
- Provide a CLI `rule` operation accepting a rule ID and showing its explanation, detection limits, and passing and failing examples.
- Separate document loading and source tracking, LaTeX scanning, rule evaluation, suppression handling, and CLI presentation. The precise internal module layout is an implementation choice.
- Keep one rule catalogue shared by evaluation, suppression validation, and rule help. Preserve guideline IDs such as `MATH-04` so findings can be traced to the source requirements.
- Do not read project-level linter configuration in the first release. The CLI ignore option and its API equivalent provide invocation-wide exclusions.

### Document loading and scanning

- Read the explicitly supplied root document and recursively follow literal LaTeX input and include commands. Preserve inclusion order for checks involving heading hierarchy and document structure.
- Collect labels and references across the document before evaluating rules that depend on them. A reference in another included file can satisfy a figure or equation reference check.
- Preserve the original filename and source position for every finding, including findings discovered through document-wide analysis.
- Report a missing included file as a check failure with its include location and unresolved target. An incomplete document must not appear to have passed.
- Use regex to recognize patterns and a small scanner to track nested braces, command arguments, math, and environments. The sample regexes in the guidelines are sketches that must be validated against examples.
- Exclude comments and literal code from ordinary style checks. Recognize escaped comment characters so source text is not accidentally discarded. Read suppression directives from actual comments only.
- Apply prose and math rules only in their relevant contexts. For example, a fraction in display math must not trigger the inline-fraction rule, and a table row break must not trigger the paragraph-break rule.
- Preserve enough source information to distinguish a genuinely blank math line from a comment-only line, which the guidelines allow.
- Support nested command arguments and ordinary multiline source. Document the concrete supported commands and environments as part of implementation.
- Do not expand user-defined macros, execute TeX, or resolve include paths constructed by macros. Document these limits without claiming equivalence to a compiled document.

### Rule scope

The first release covers mechanical checks on LaTeX source and bounded style heuristics. A guideline's regex-linter tag alone does not make every part of that guideline implementable. Rule help must state which requirement is checked and which parts still need review.

The following table records the agreed coverage by guideline family. It specifies the source-check boundary rather than promising semantic understanding.

| Guideline IDs | First-release coverage |
| --- | --- |
| STRUC-02, STRUC-03 | Excessive numbered heading depth and isolated subheadings, using the document hierarchy. |
| STRUC-06 | Sections ending in a recognized equation, list, table, or figure block. The check cannot establish that the final prose is a complete sentence. |
| PROSE-02 | Heuristic detection of standalone This or These using documented patterns. |
| PROSE-03 | Suspected comma-before-that violations in prose, with wording that acknowledges grammatical ambiguity. |
| PROSE-04 | Heuristic American headline capitalization checks in heading text. Document treatment of acronyms, math, and commands. |
| PROSE-07 | A colon immediately before a recognized displayed equation. Broader grammatical integration remains a review task. |
| CITE-04 | A citation placed after the sentence's terminal period. Whether it substantiates the right claim remains a review task. |
| MATH-01 | Required terminal punctuation and thin spacing in supported displayed-math environments. Grammatical choice of punctuation remains a review task. |
| MATH-02 | Numbered equations lacking a recognized document reference. Document supported numbering, labels, and multiline environments. |
| MATH-03 | Equation-reference syntax and redundant equation wording, accounting for the sentence-start exception. |
| MATH-04 | Fractions in inline math. |
| MATH-06 | Recognizable number-unit spacing violations. Do not infer ambiguous variable products or physical meaning. |
| MATH-09 | Recognizable programming operators used in math. Ordinary LaTeX command backslashes must not be treated as programming operators. |
| MATH-12 | Recognizable standard function or operator notation that should be upright. Do not infer whether an arbitrary letter denotes a constant. |
| MATH-13 | Blank lines inside supported math environments, allowing comment-only lines. |
| MATH-14 | Suspected decimal commas in English math, with documented detection limits. |
| FIG-03 | Figure environments, required unique figure labels, and document-wide references. |
| FIG-06 | Caption presence and a final full stop. Caption comprehensiveness remains a review task. |
| FIG-07, FIG-08 | Caption and label order, centering, and use of a center environment inside a figure float. |
| TAB-01 | Forbidden vertical rules and recognized departures from the prescribed booktabs commands. |
| TAB-02, TAB-03 | Table caption and label order, and centering. |
| TYPO-01 through TYPO-04 | Recognizable nonbreaking and thin-space conventions, plus swallowed spaces after known parameterless commands. |
| TYPO-05 | Recognizable text negatives and numeric ranges using the wrong dash notation. |
| TYPO-06 | Straight quotation marks in English prose, excluding literal code and escaped command syntax. |
| TYPO-07 | Explicit forbidden emphasis commands and combinations detectable from source. |
| TYPO-08 | Explicit line-break commands used as paragraph breaks in running text. |
| TYPO-09 | Standard label prefixes, using context where it is available. |
| WORK-03 | Explicit document-class options that violate final-submission requirements. Do not infer class defaults or effective page geometry without parsing the class. |

Semantic distinctions such as counting indices versus descriptive subscripts in MATH-08 remain outside the first release. No rule may claim to enforce an entire guideline when it only checks one mechanical aspect.

All implemented rules run by default. Heuristics do not form a separate opt-in group. Their messages and rule explanations identify the suspected problem and known limits; suppressions handle intentional exceptions.

### Findings and explanations

- Each finding includes a rule ID, original source filename, line and column, concise explanation, source excerpt, and suggested correction. Use one-based positions consistently in the API and CLI.
- Return findings in a deterministic order. Equivalent API and CLI invocations must agree on rule IDs and locations.
- Attach each finding to an actionable source location. For a missing construct, use the relevant existing command or environment. Document these locations so same-line suppression is predictable.
- Keep short diagnostics readable without requiring the author to open the full guidelines. Describe uncertain grammatical or stylistic findings as suspected violations.
- Each implemented rule has a longer explanation, passing and failing examples, and an explicit statement of partial coverage or heuristics where applicable. Expose rule information through the library as well as CLI help.
- The CLI succeeds only when the check completes without unsuppressed findings or input errors. Findings, unknown rule IDs, and missing files must produce a nonzero exit status. Exact nonzero status values are an implementation detail to document and test.

### Suppressions

- Use the `latex-lint` namespace for all source directives. Each directive is a LaTeX comment with an action, an equals sign, and a comma-separated list of explicit rule IDs.
- The `ignore` action suppresses findings whose reported location is on the same source line. It does not mean ignore the next line.
- The `disable` action suppresses the named rules from its position until a corresponding `enable` action or the end of that file.
- The `enable` action ends the file-local disabled state for the named rules. It does not override invocation-wide exclusions.
- Source directives affect only their own file. A parent's disabled state does not carry into included files, and a directive in an included file does not change its parent's state.
- Invocation-wide exclusions apply to every loaded file. The CLI option and Python API argument have equivalent behavior.
- Require explicit rule IDs. Unknown IDs in source directives or invocation arguments produce an error rather than silently doing nothing.
- Use these same mechanisms for German passages such as the abstract. Automatic language detection is not required.

## Testing Decisions

Every rule must have focused unit tests. These tests can run one rule through the public checking API with other rules ignored, or through a stable rule-evaluation interface where that is clearer. They must assert observable findings rather than regex strings, private scanner state, or the chosen module layout.

- Give every rule at least a violating example and a valid counterpart. Add relevant edge cases such as comments, literal code, nesting, optional arguments, multiline source, and context boundaries. Do not mechanically repeat irrelevant cases for every rule.
- For heuristics, test documented exceptions and ensure the explanation conveys uncertainty. A test should establish the intended boundary of detection.
- Assert rule IDs, actionable source positions, and useful correction information. Avoid snapshots of incidental terminal whitespace unless presentation itself is under test.
- Test document loading and combined rule evaluation through the public API with small thesis fixtures. Cover included files, references across files, heading hierarchy across includes, and missing-file failures.
- Test source-position preservation for nested arguments, removed comments, and included files. Add direct scanner tests only where they clarify an otherwise difficult-to-observe case.
- Test suppression behavior through resulting findings. Cover same-line ignore, disable and enable regions, end-of-file scope, multiple IDs, file isolation, invocation-wide exclusions, and unknown IDs.
- Test the CLI through its user-facing interface. Cover a clean document, a failing document, diagnostic presentation, ignore arguments, invalid inputs, and rule explanations. These tests use the development environment; they do not install into another project on every run.
- Check that the rule catalogue, rule help, and implemented checks agree. Every advertised rule must be implemented, documented, and covered by focused tests.

The repository already uses pytest, temporary-fixture support from pytest, and a pre-commit gate that includes linting, type checking, and tests. Its greeting tests provide only basic test-runner precedent; there is no existing linter behavior to preserve. Start implementation with failing tests that make the intended behavior verifiable, iterate with targeted checks, and finish with the repository's full gate.

Installation into another uv project is a manual release check. Create a separate temporary project, add this repository as a dependency, import its public API, run the installed console command against a small thesis, and inspect rule help. Run from outside the library checkout so local imports cannot conceal a packaging problem. Record the result with release validation. This does not need to become an automated test in the first release.

## Out of Scope

- Semantic review of claims, citation support, plagiarism, argument structure, caption quality, variable meanings, or prose quality beyond the documented heuristics.
- Bibliography parsing and metadata checks.
- Checking generating scripts, generated figures, plot appearance, or other assets on disk. Reading the thesis root and included source files is still required.
- TeX compilation, compilation-log analysis, PDF layout, PDF/A validation, and inspection of build pipelines.
- General-purpose TeX interpretation, macro expansion, or dynamically constructed include targets.
- Automatic source fixes or formatting.
- Project configuration tables, configurable rule definitions, third-party rule plugins, and language profiles.
- Editor integrations, a language server, watch mode, package-index publication, and automated testing of installation into an independent project.

## Further Notes

This specification records the design agreed in the interview, including the correction that every implemented rule is on by default. It also records the author's requirement for per-rule unit tests and the decision to verify installation manually.

The thesis guidelines remain the source of rule intent. Their sample patterns sometimes cover only part of the prose requirement or match valid LaTeX. During implementation, preserve the requirement, document detection boundaries, and use examples to validate the check instead of copying a pattern uncritically.

The author requested a specification only at this stage. Creating this document does not authorize implementation. No linter source code, dependency changes, or packaging changes are part of this task.
