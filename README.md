# latex-linting

Linting plus review agents for thesis writing

## Check a document

Requires Python 3.13 or later. From this checkout:

```bash
uv sync
uv run latex-lint check path/to/thesis.tex
uv run latex-lint check --ignore MATH-04 path/to/thesis.tex
uv run latex-lint rule MATH-04
```

Installing this package also installs the `latex-lint` command. The root document
is required and must be UTF-8. The checker follows literal `\input` and `\include`
commands recursively from the supplied root. It never changes source files,
compiles TeX, or expands macros.

Exit codes are `0` for a clean check or successful rule help, `1` for findings,
and `2` for input errors such as unreadable files, missing included files, invalid UTF-8,
missing arguments, or unknown rule IDs. Findings go to stdout; input errors go to stderr.
This is a style checker, not a LaTeX syntax validator.

### Python interface

```python
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule

findings = check("path/to/thesis.tex")
findings_filtered = check("path/to/thesis.tex", ignored_rules=["MATH-04"])
rule = get_rule("MATH-04")
```

`check` accepts a string or `pathlib.Path` along with an optional `ignored_rules`
collection of rule IDs to exclude invocation-wide, returning a list of immutable `Finding`
objects without printing. Each has `rule_id`, `filename`, `line`, `column`,
`excerpt`, `explanation`, and `correction` fields. The filename retains the supplied
path. Lines and columns are one-based; columns count Unicode characters, with a tab
counting as one character. The excerpt is the original line without its line ending.
Findings preserve document reading order across included files, and within each file are
ordered by line, column, then rule ID. File and decoding errors propagate
as `OSError` and `UnicodeError`; unresolved included files raise `MissingIncludeError`
(a subclass of `FileNotFoundError`). Unknown rule IDs in `ignored_rules` or in-source
directives raise `ValueError`. `get_rule` raises `KeyError` for an unknown ID.

### Rule suppressions

Authors can suppress specific rule violations using in-source comments or invocation-wide exclusions.

#### Source directives

Directives use the `latex-lint` namespace followed by a colon, an action (`ignore`, `disable`, or `enable`), an equals sign, and comma-separated rule IDs (optional whitespace is permitted around `:`, `=`, and `,`):

- `% latex-lint:ignore=MATH-04`: Suppresses findings reported on its own source line only. It does not suppress findings on the following line.
- `% latex-lint:disable=MATH-04`: Disables the specified rules from the directive's position until a corresponding `enable` directive or the end of the source file.
- `% latex-lint:enable=MATH-04`: Re-enables the specified rules from that position forward for file-local checks.

Directives must be actual LaTeX comments; directive-like text inside literal code (such as `verbatim`, `lstlisting`, or `\verb`) has no suppression effect. Unknown rule IDs in directives produce an error and cannot yield a successful check.

#### Reported-location semantics

Same-line `ignore` directives evaluate against each finding's reported source line. A finding is suppressed if an `ignore` directive naming its rule appears on that exact line. Findings reported on subsequent lines are not suppressed.

#### Invocation-wide exclusions

Pass `--ignore` with comma-separated IDs to the CLI `check` command or `ignored_rules` to `check(...)` in Python:

```bash
uv run latex-lint check --ignore MATH-04 path/to/thesis.tex
```

Invocation-wide exclusions apply across all files and cannot be undone by in-source `enable` directives.

#### Excluding German passages

For passages written in German, such as the German abstract (*Zusammenfassung*), wrap the passage with file-local directives:

```latex
% latex-lint:disable=MATH-04
% German abstract or chapter text
% latex-lint:enable=MATH-04
```

If an entire file or chapter is in German, place the `disable` directive at the top of that file, or pass the rule IDs to `--ignore` across the check invocation.

### Multi-file documents

The checker recursively follows literal `\input{...}` and `\include{...}` commands
from the root document:

- **Path resolution**: Relative paths resolve first against the directory of the file
  containing the include command. If unresolved and different, resolution falls back
  to the root document directory.
- **Omitted extensions**: If a target has no `.tex` extension, the checker attempts
  resolution with `.tex` appended when the path without extension does not exist.
- **Dynamic targets**: Targets constructed by macros (e.g. `\input{\mychapter}`) are
  not expanded and report an unresolved include error.
- **Comments and literals**: Include commands inside comments or literal environments
  (`verbatim`, `lstlisting`, `minted`, `\verb`) are ignored and do not load files.
- **Suppression isolation**: Source directives affect only their containing file. A
  parent's disabled rules do not carry into included files, child directives do not
  alter the parent's state, and returning to the parent restores that file's own state.
- **Missing targets**: Missing included files raise `MissingIncludeError` identifying
  the include location and unresolved target. The CLI reports the error to stderr
  and exits with code `2`.

### MATH-04 support

MATH-04 is enabled by default and reports each `\frac` command in inline math at
its backslash. Use `$a/b$`, `$s^{-1}$`, or move the fraction into display math.
Nested arguments and multiline math are supported, with a finding for each nested
`\frac` as well.

| Context | Supported syntax |
| --- | --- |
| Inline math | `$...$`, `\(...\)`, `\begin{math}...\end{math}` |
| Display math | `$$...$$`, `\[...\]`, `displaymath`; `equation`, `align`, `alignat`, `gather`, `multline`, `flalign`, `eqnarray`, and their starred forms |
| Comments | Unescaped `%` through the end of the line |
| Literal code | `\verb`, `\verb*`, and environments `verbatim`, `verbatim*`, `lstlisting`, `minted` |

Escaped `%` and `$` retain their literal meaning. Comments and literal code cannot
open or close math. Environment names must be literal; comments within a
`\begin{...}` or `\end{...}` command are unsupported. The checker does not interpret
text-mode command arguments such as `\text{...}`, user-defined commands or environments,
or alternative fractions such as `\dfrac` and `\tfrac`.
Unclosed math extends to the end of the file. An unclosed literal environment hides
the remainder of the file, while an unclosed `\verb` ends at the line boundary.
Rule help includes examples and these detection limits.

### STRUC-02 support

STRUC-02 is enabled by default and reports numbered headings deeper than subsection (`\subsubsection`, `\paragraph`, `\subparagraph`) at the command backslash. Use unnumbered headings (`\subsubsection*`, `\paragraph*`, `\subparagraph*`) or restructure the hierarchy to stay within three numbered levels (`\chapter`, `\section`, `\subsection`). Optional arguments (e.g. `\subsubsection[short]{Long}`) are supported. Comments and literal blocks are excluded.

### STRUC-03 support

STRUC-03 is enabled by default and reports parents with exactly one numbered child at the relevant level (e.g. a `\chapter` with only one `\section`, or a `\section` with only one `\subsection`). A second child satisfies the rule even when it appears in another included source file. Findings are attached to the isolated child heading command backslash, allowing same-line `% latex-lint:ignore=STRUC-03` suppressions in the child's source file. Starred headings are unnumbered and do not participate in numbered hierarchy counting.

### WORK-03 support

WORK-03 is enabled by default and detects explicitly forbidden document-class options (`draft`, `oneside`, `nohyperref`) inside `\documentclass[...]`. Options are recognized as comma-separated items rather than arbitrary substrings, so options like `draftcopy` or `myoneside` are not flagged, nor are disabled key-value options like `draft=false`. Multiline option declarations are supported and findings point to the forbidden option item, enabling same-line suppression on that line. WORK-03 does not establish class defaults, effective page dimensions, or complete submission compliance.

### PROSE-02 support

PROSE-02 is enabled by default and detects standalone "This" or "These" without an explicit referent noun at sentence start or after punctuation immediately followed by common verbs (`is`, `shows`, `demonstrates`, etc.). Demonstratives followed by a referent noun pass (e.g. "This approach", "These results"). Findings point to the demonstrative, enabling same-line suppression.

### PROSE-03 support

PROSE-03 is enabled by default and detects suspected comma-before-that constructions in English prose. It reports the comma, acknowledging grammatical ambiguity between restrictive clauses and parenthetical phrases or idioms. Comments, math mode, literal code, and command syntax arguments are excluded.

### PROSE-04 support

PROSE-04 is enabled by default and checks American headline capitalization in supported LaTeX headings (`\chapter`, `\section`, `\subsection`, etc., including starred forms). First and last words must be capitalized. Minor words (articles, conjunctions, short prepositions <= 4 letters) must be lowercase in interior positions. Hyphenated compound words, all-uppercase acronyms (e.g. `API`, `CNN`), math ($...$), and commands inside headings are handled without false flags. Findings attach to the heading command backslash.

### CITE-04 support

CITE-04 is enabled by default and detects recognized citation commands (`\cite`, `\citep`, `\citet`, `\autocite`, etc., including optional arguments like `[p.~5]`) immediately following a sentence's terminal period in text mode, recommending moving the citation before the period. Common abbreviations like `et al.` are excluded from sentence-terminal detection. Findings attach to the citation command backslash.

### MATH-01 support

MATH-01 is enabled by default and checks for required terminal punctuation (`.`, `,`, `;`, `:`, `!`, `?`) preceded by thin spacing (`\,`) in supported displayed-math environments (`equation`, `align`, `gather`, `multline`, `alignat`, `flalign`, `eqnarray`, their starred forms, `displaymath`, `\[...\]`, and `$$...$$`). In multiline equations, the terminal position of the final line before closing is checked. Trailing labels, comments, whitespace, and line breaks (`\\`) are ignored. Findings attach to the closing delimiter or environment command, allowing same-line suppression. The rule does not infer grammatical appropriateness or rendered layout.

### MATH-13 support

MATH-13 is enabled by default and detects genuinely blank lines inside supported math environments (`equation`, `align`, `gather`, `multline`, `alignat`, `flalign`, `eqnarray`, their starred forms, `displaymath`, `\[...\]`, and `$$...$$`). Comment-only lines starting with `%` are explicitly permitted for visual code organization and are not flagged. Findings attach to column 1 of the blank line.

### PROSE-07 support

PROSE-07 is enabled by default and reports a colon in text mode immediately preceding a recognized displayed equation (`\[`, `$$`, or display math environments like `equation`, `align`, `gather`). Comments and whitespace between the colon and the equation are allowed. Findings attach to the colon, enabling same-line suppression. The rule checks the mechanical occurrence of the colon and does not claim to evaluate entire surrounding sentence grammar.

### STRUC-06 support

STRUC-06 is enabled by default and reports a chapter, section, subsection, or subsubsection ending directly on a recognized display math equation, list (`itemize`, `enumerate`, `description`), table (`table`, `tabular`, `tabularx`, etc.), or figure environment before the next heading or document end (`\end{document}` or EOF). Document reading order across included files is respected: a prose continuation in an included file satisfies the rule. Trailing labels, comments, whitespace, and page-break commands do not count as final prose. Findings attach to the ending block command, allowing same-line suppression.

### MATH-06 support

MATH-06 is enabled by default and reports number-unit spacing violations in math mode where a number is directly adjacent to or separated only by regular whitespace from recognized units (`\mathrm{...}`, `\text{...}`, or bare units like `kg`, `Hz`, `kHz`, `MHz`, `GHz`, `mm`, `cm`, `km`, `mV`, `mA`, `kW`, `MW`, `ms`, `rad`, `deg`, `dB`). Recommends inserting a thin space `\,` (e.g. `10\,\mathrm{kg}`, `10\,\text{m}`) or using `siunitx` commands (`\SI`, `\qty`, `\unit`). Does not infer ambiguous variable products (e.g. `2x`, `3a`, `4y`) or bare single-letter symbols (`10m`, `5s`) without `\mathrm` or `\text`. Findings attach to the number start, enabling same-line suppression. Comments, literal code, and nested non-math commands are excluded.

### MATH-09 support

MATH-09 is enabled by default and detects documented programming operators in math mode (`*`, `!=`, `==`, `&&`, `||`, `<=`, `>=`, `~=`, `.*`, `.^`, `./`, `**`) where LaTeX mathematical notation should be used (such as `\cdot`, `\neq`, `=`, `\land`, `\lor`, `\le`, `\ge`). Ordinary LaTeX command backslashes (e.g. `\cdot`, `\alpha`, `\frac`) and superscript/subscript asterisks (e.g. `x^*`, `x^{*}`) are accepted and never flagged. Findings attach to the operator, enabling same-line suppression. Comments, literal code, and nested non-math commands are excluded.

### MATH-12 support

MATH-12 is enabled by default and detects recognized standard mathematical functions and operators (`sin`, `cos`, `tan`, `exp`, `ln`, `log`, `min`, `max`, `sup`, `inf`, `lim`, `det`, `arg`, `deg`, etc.) written as italic text in math mode instead of standard LaTeX upright commands (e.g. `\sin`, `\cos`, `\exp`, `\lim`, `\min`). Upright macros and arguments of `\mathrm`, `\operatorname`, or `\text` are accepted. Arbitrary single-letter symbols (such as constants `e` or `i`) are not inferred. Findings attach to the function name, enabling same-line suppression. Comments, literal code, and nested non-math commands are excluded.

### MATH-14 support

MATH-14 is enabled by default and detects adjacent digits separated by a comma without whitespace (`\d+,\d+`) in math mode (e.g. `$3,14$`). In English math, a decimal period should be used (e.g. `$3.14$`). Decimal commas wrapped in braces (e.g. `$3{,}14$`) are accepted for localized notation. The diagnostic explains ambiguity where unspaced comma-separated lists or coordinates (e.g. `$(1,2)$`) resemble decimals, recommending spaces after commas. Findings attach to the comma, enabling same-line suppression. Comments, literal code, and nested non-math commands are excluded.

### MATH-02 support

MATH-02 is enabled by default and detects numbered display math equations (`equation`, `align`, `gather`, `multline`, `alignat`, `flalign`, `eqnarray`) declaring labels that are never referenced across the loaded document. Recognized reference commands include `\ref`, `\eqref`, `\autoref`, `\cref`, and `\Cref`, and references across included source files (forward and backward) satisfy the rule. Findings attach to the unreferenced `\label` command, allowing same-line suppression. Unnumbered environments (`equation*`, `align*`, `gather*`, `\[...\]`, `$$...$$`) do not require references. Unlabeled numbered equations are not flagged because equations are evaluated through declared `\label` keys. References and labels in comments or literal code are excluded.

### MATH-03 support

MATH-03 is enabled by default and detects redundant equation wording and incorrect equation-reference syntax in running text. It flags words like "equation", "eq.", "Equation", "Eq.", "Gleichung", and "Gl." immediately preceding `\eqref` or `\ref`, except when capitalized at sentence start (e.g. "Equation~\eqref{...}"). It also flags `\ref` used to reference equation labels and parenthesized references `(\ref{...})`, recommending `\eqref{...}`. Findings attach to the redundant word or the reference command, enabling same-line suppression. Comments, literal code, and math mode are excluded.

### TYPO-09 support

TYPO-09 is enabled by default and checks standard label prefixes in `\label{...}` commands based on structural context. In known contexts, labels must use standard prefixes: `fig:` inside figure environments (`figure`, `figure*`), `tab:` inside table environments (`table`, `table*`), `eq:` inside display math environments, `ch:` or `cha:` immediately following `\chapter`, and `sec:` immediately following `\section`, `\subsection`, or `\subsubsection` (with `app:` also permitted for appendix sections and chapters). In unknown contexts outside these environments and headings, labels must start with one of the standard prefixes (`ch:`, `cha:`, `sec:`, `fig:`, `tab:`, `eq:`, `app:`, `lst:`, `listing:`). Findings attach to the `\label` command, allowing same-line suppression. Comments and literal code are excluded.

### FIG-03 support

FIG-03 is enabled by default and ensures that figure content (`\includegraphics`, `\begin{tikzpicture}`) floats in a `figure` or `figure*` float environment, that every figure declares a `\label`, that figure labels are unique across the entire document, and that declared figure labels are referenced in the body text using recognized reference commands (`\ref`, `\autoref`, `\cref`, `\Cref`). References collected from other included sources satisfy the check. References in comments and literal code do not count. Findings attach to the `\includegraphics` or `\begin{tikzpicture}` token when outside floats, to `\begin{figure}` or `\begin{figure*}` when missing a label, or to `\label` for duplicate or unreferenced labels, enabling same-line suppression.

### FIG-06 support

FIG-06 is enabled by default and checks that every `figure` and `figure*` float environment has a `\caption{...}` command, and that the caption text terminates with a full stop (`.`). Optional short captions (`\caption[short]{full text.}`), multiline captions, nested formatting, and nested `\label` declarations are supported. Findings attach to `\begin{figure}` when missing a caption, or to `\caption` when missing a terminal full stop, enabling same-line suppression. The rule does not evaluate caption comprehensiveness or semantic quality.

### FIG-07 support

FIG-07 is enabled by default and checks the standard ordering inside `figure` and `figure*` environments: image content (`\includegraphics`, `\begin{tikzpicture}`, or included graphics like `\input{...}`), followed by `\caption{...}`, followed or enclosed by `\label{...}`. Captions placed above any image content are flagged at `\caption`, and labels placed before `\caption` are flagged at `\label`. Labels placed inside `\caption{...}` are supported and accepted. Same-line suppressions are supported on the respective command lines.

### FIG-08 support

FIG-08 is enabled by default and enforces proper centering of figure floats. It rejects the `center` environment (`\begin{center}...\end{center}`) inside `figure` and `figure*` floats because it introduces unwanted vertical whitespace, recommending `\centering` instead. It also flags figure floats that lack a `\centering` declaration. Findings attach to `\begin{center}` when the environment is used, or to `\begin{figure}` or `\begin{figure*}` when `\centering` is missing, enabling same-line suppression.

## Code structure

The public checking interface is `check(root)`; internal scanning and evaluation
interfaces can evolve as the remaining tickets are implemented.

- `source.py` owns original text, line indexing, and immutable findings. Offsets
  refer to unchanged source, including CRLF line endings.
- `scanner.py` emits tokens with source spans and math context. Comments, literal
  code, commands, environment delimiters, braces, and ordinary text remain distinct.
  Rules do not have to rediscover comment escaping or math delimiters.
- `rules/` contains one module per rule, such as `math_04.py`, with its evaluator
  and help text together. `model.py` defines the shared `Rule` type;
  `catalogue.py` explicitly registers each implemented rule in `RULES` and exposes
  `get_rule`. Both checking and rule help use this catalogue. Rule modules do not
  import the catalogue, so adding rules does not create circular imports.
- `main.py` loads, scans, evaluates, and orders findings. It owns file I/O; the
  scanner and rules operate on in-memory values.
- `suppression.py` parses in-source directives from comment tokens, validates rule IDs,
  and filters findings according to same-line ignore, file-local disable/enable ranges,
  and invocation-wide exclusions.
- `cli.py` parses arguments, renders results, and maps errors to exit codes.

For ticket 02, comment tokens allow suppression directives to be read without
confusing literal code for comments. Findings retain the source location needed
for same-line and file-local suppression. Ticket 03 can load separate source
objects in inclusion order instead of concatenating files and losing their origins.
Later reference and structural rules will need a document-wide collection pass
before evaluation. These changes belong inside the checking implementation and
do not require callers to manage scanner state or rule execution order.

This version has no plugin framework, full LaTeX syntax tree, or configurable rule
pipeline. The scanner handles the context this ticket needs; later syntax support
should be added with behavior tests for the rule that needs it.

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management, [ruff](https://github.com/astral-sh/ruff) for linting and formatting, and pre-commit hooks to automate code quality checks.

### Setup

1. Install `uv`:

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. Clone the repo:

    ```bash
    git clone https://github.com/<user_name>/latex_linting.git
    ```

    and navigate to it:

    ```bash
    cd latex_linting
    ```

3. Sync dependencies:

    ```bash
    uv sync
    ```

4. Set up pre-commit hooks (this will run linting, formatting, and tests on every commit):

    ```bash
    uv run pre-commit install
    ```

### Running Tests

To run tests manually using `pytest` (otherwise pre-commit will run them):

```bash
uv run pytest
```

### Linting and Formatting

To check for linting errors:

```bash
uv run ruff check .
```

To format code:

```bash
uv run ruff format .
```

### Type checking

```bash
uv run ty check .
```
