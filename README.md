# latex-linting

Linting plus review agents for thesis writing

## Installation and Usage

Requires Python 3.13 or later.

### Installation via uv

To add `latex-linting` as a dependency to another thesis project using [uv](https://github.com/astral-sh/uv):

```bash
# Add from a local checkout:
uv add /path/to/latex_linting

# Or add from a git repository:
uv add git+https://github.com/<user_name>/latex_linting.git
```

From within this repository checkout:

```bash
uv sync
```

### Command-line interface

Installing the package provides the `latex-lint` console command:

```bash
# Check a thesis root document:
latex-lint check path/to/thesis.tex

# Or check a bibliography file directly:
latex-lint check path/to/references.bib

# Check with invocation-wide rule exclusions:
latex-lint check --ignore MATH-04,PROSE-02 path/to/thesis.tex

# Inspect rule documentation, examples, and limits:
latex-lint rule MATH-04

# Install bundled agent skills into project .agents/skills/:
latex-lint install-skills

# Install using a preset (local, global, claude, claude-global):
latex-lint install-skills global

# Install into a custom directory (use --force to overwrite existing):
latex-lint install-skills --dest path/to/skills --force
```

When running within a `uv` project without global installation, prefix commands with `uv run` (e.g. `uv run latex-lint check path/to/thesis.tex`).

#### Explicit root selection

The `check` command requires an explicit path to the root document (`.tex`) or bibliography file (`.bib`). It never infers, searches, or guesses the root document from the current working directory. The root document and all included files must be UTF-8 encoded. The checker recursively follows literal `\input{...}` and `\include{...}` commands from the root, as well as `\addbibresource{...}` and `\bibliography{...}` declarations. It never alters source files, compiles TeX, or expands macros.

#### Exit codes and failure behavior

- `0`: Clean check (no unsuppressed findings) or successful `rule` documentation output.
- `1`: Check completed with unsuppressed findings. Findings are formatted and printed to `stdout`.
- `2`: Input or configuration error. Diagnostics are printed to `stderr`. This includes:
  - Missing or inaccessible root document (`FileNotFoundError` / `OSError`).
  - Missing included file (`MissingIncludeError`).
  - Invalid UTF-8 encoding (`UnicodeError`).
  - Unknown rule ID passed to `--ignore` or used in an in-source directive (`ValueError`).
  - Missing command-line arguments or invalid options.

### Python API

The public checking API is provided by `latex_linting.main`:

```python
from latex_linting.main import Finding, check
from latex_linting.rules.catalogue import get_rule

# Check a document:
findings: list[Finding] = check("path/to/thesis.tex")

# Check with invocation-wide exclusions:
findings_filtered: list[Finding] = check(
    "path/to/thesis.tex",
    ignored_rules=["MATH-04", "PROSE-02"],
)

# Inspect rule details:
rule = get_rule("MATH-04")
```

`check(root, ignored_rules=None)` accepts a string path or `pathlib.Path` and an optional collection of rule ID strings. It returns an immutable list of `Finding` objects without printing to terminal streams.

Each `Finding` has the following attributes:

- `rule_id`: The unique rule identifier (e.g. `"MATH-04"`).
- `filename`: The path to the file containing the finding (retains the supplied path format).
- `line`: One-based line number.
- `column`: One-based column number (counts Unicode characters; tab counts as one character).
- `excerpt`: The exact source line without trailing line endings.
- `explanation`: Explanation of the rule violation.
- `correction`: Actionable suggestion for resolving the violation.

Findings preserve document inclusion order across multi-file documents, and within each file are sorted deterministically by `(line, column, rule_id)`.

### Rule suppressions

Authors can suppress specific rule violations using in-source comments or invocation-wide exclusions.

#### Source directives

Directives use the `latex-lint` namespace followed by a colon, an action (`ignore`, `disable`, or `enable`), an equals sign, and a comma-separated list of explicit rule IDs (whitespace around `:`, `=`, and `,` is tolerated):

- `% latex-lint:ignore=MATH-04,MATH-12`: Suppresses findings reported on its own source line only. It does not affect findings on subsequent lines.
- `% latex-lint:disable=MATH-04,TYPO-06`: Disables the listed rules from the directive's location until a corresponding `enable` directive or the end of the file.
- `% latex-lint:enable=MATH-04,TYPO-06`: Re-enables the listed rules from that point onward within the file.

Directives must appear as actual LaTeX comments. Text resembling directives inside literal code environments (`verbatim`, `lstlisting`, `minted`, `\verb`) has no suppression effect. Unknown rule IDs in directives produce a `ValueError` (exit code `2`) to prevent typos from silently hiding checks.

#### Reported-location semantics

Same-line `ignore` directives evaluate against each finding's reported source line. A finding is suppressed if an `ignore` directive naming its rule appears on that exact line. Targeted exclusions leave unrelated rules active on the same line.

#### File isolation

Source directives affect only their containing file. A parent file's disabled rules do not carry into included files, child file directives do not alter the parent file's suppression state, and returning from an include restores the parent file's state.

#### Invocation-wide exclusions

Pass `--ignore` with comma-separated IDs to the CLI or `ignored_rules` to `check(...)` in Python:

```bash
latex-lint check --ignore MATH-04,PROSE-02 path/to/thesis.tex
```

Invocation-wide exclusions apply across all files and cannot be overridden by in-source `enable` directives. Targeted exclusions leave all other rules active.

#### Excluding German passages

For sections written in German, such as the German abstract (*Zusammenfassung*), wrap the passage with file-local directives:

```latex
% latex-lint:disable=PROSE-02,PROSE-03,TYPO-03,TYPO-06
% Deutsche Zusammenfassung...
% latex-lint:enable=PROSE-02,PROSE-03,TYPO-03,TYPO-06
```

If an entire file is in German, place the `disable` directive at the top of that file, or pass the relevant rule IDs to `--ignore` across the invocation.

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

### CITE-08 support

CITE-08 is enabled by default and validates the completeness of mandatory BibLaTeX metadata fields per entry type in `.bib` files. It checks `author` (or `editor`, `organization`, or `institution` where appropriate), `title`, and `year` (or `date`/`urldate`) across all entry types; `journal` (or `journaltitle`), `volume`, `pages`, and `doi` for `@article`; `publisher` and `isbn` for `@book`; `booktitle`, `pages`, and `doi` or `isbn` for `@inproceedings`; and respective publication venues for other types. Non-citation entries (`@comment`, `@string`, `@preamble`) are ignored. Bibliography files are discovered automatically via `\addbibresource`, `\bibliography`, or `\addglobalbib` in the LaTeX document hierarchy, or can be checked directly by passing a `.bib` file to `latex-lint check`. Missing required fields are reported at the entry's `@` declaration, allowing same-line `% latex-lint: ignore=CITE-08` suppressions when DOI or ISBN identifiers are unassigned.

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

### TAB-01 support

TAB-01 is enabled by default and enforces booktabs conventions in table specifications. It detects vertical rules (`|`) in column specifications of supported tabular environments (`tabular`, `tabular*`, `tabularx`, `tabulary`, `longtable`), including nested repetition constructs (`*{...}{...}`) and optional placement arguments (`[t]`, `[b]`, `[c]`). It also flags forbidden horizontal rules inside tabular environments (`\hline` recommending `\toprule`, `\midrule`, or `\bottomrule`; and `\cline` recommending `\cmidrule`). Unrelated vertical bars outside column specifications—such as math-mode vertical bars (`$|x|$`), text-mode pipe characters, literal code, or comments—are never flagged. Findings attach to the `|` character or the `\hline` / `\cline` command token, enabling same-line suppression. The rule does not inspect semantic column units or rendered table layout.

### TAB-02 support

TAB-02 is enabled by default and verifies component ordering inside `table` and `table*` float environments. Table captions must precede tabular content (`tabular`, `tabular*`, `tabularx`, `tabulary`, `longtable`), and table labels must follow or be enclosed within `\caption{...}` (`\caption{... \label{...}}`). Captions placed after tabular content are flagged at `\caption`, and labels placed before captions are flagged at `\label`. Standalone tabulars outside floats are not checked. Findings attach to `\caption` or `\label`, enabling same-line suppression.

### TAB-03 support

TAB-03 is enabled by default and enforces proper centering of table floats. It rejects the `center` environment (`\begin{center}...\end{center}`) inside `table` and `table*` float environments because it introduces unwanted vertical whitespace, recommending `\centering` instead. It also flags table floats that lack a `\centering` declaration. Findings attach to `\begin{center}` when the environment is used, or to `\begin{table}` / `\begin{table*}` when centering is missing, enabling same-line suppression. Center environments in regular text outside table floats are not flagged.

### TYPO-01 support

TYPO-01 is enabled by default and checks for a nonbreaking space (`~`) before supported reference commands (`\ref`, `\eqref`, `\autoref`, `\cref`, `\Cref`, `\pageref`) and citation commands (`\cite`, `\citep`, `\citet`, `\autocite`, `\parencite`, `\textcite`, `\footcite`, `\fullcite`, `\nocite`, `\citeauthor`, `\citeyear`) where prose calls for a preceding space. It flags regular space (` `) or newline characters preceding the command without `~`. Commands at prose boundaries (beginning of line across sentence starts, beginning of sentence, or after opening parentheses, brackets, or braces like `(\ref{...})`, `[\cite{...}]`, `{\ref{...}}`) or already preceded by `~` pass. Optional arguments (`\cite[p.~5]{...}`) and multiline input are supported. Findings attach to the command start, enabling same-line suppression. Comments, literal code (`verbatim`, `lstlisting`, `minted`, `\verb`), syntax command arguments (`\label{...}`, `\url{...}`), and math mode are excluded.

### TYPO-02 support

TYPO-02 is enabled by default and checks for nonbreaking spaces in documented fixed expressions and recognizable number-unit forms in text mode. Fixed expressions include category nouns with numbers (`Figure 1`, `Table 1`, `Section 1`, `Chapter 1`, `Fig. 1`, `Tab. 1`, `Sec. 1`, `Ch. 1`, `Eq. 1`, `Page 1`, `p. 1`, and their plural forms), titles with names (`Dr. Smith`, `Prof. Jones`, `Mr. White`, `Mrs. White`, `Ms. Davis`), and times (`3 p.m.`, `10 a.m.`, `3 Uhr`). Recognizable number-unit forms in text mode include numbers followed by physical units (`m`, `km`, `cm`, `mm`, `kg`, `g`, `s`, `ms`, `V`, `mV`, `kV`, `A`, `mA`, `W`, `kW`, `Hz`, `kHz`, `MHz`, `GHz`, `Pa`, `bar`, `dB`, etc.) separated by regular whitespace instead of a nonbreaking space (`~`), thin space (`\,`), or unit command (`\SI`, `\qty`, `\unit`). Non-unit phrases like `10 apples` and years like `in 2020` pass. Findings attach to the start of the expression or number, enabling same-line suppression. Comments, literal code, syntax arguments, and math mode are excluded.

### TYPO-03 support

TYPO-03 is enabled by default and enforces the prescribed thin space (`\,`) within supported English abbreviations in text mode: `e.\,g.` and `i.\,e.` (including capitalized forms `E.\,g.` and `I.\,e.`). It flags occurrences written without spacing (`e.g.`, `i.e.`), with regular whitespace (`e. g.`, `i. e.`), or with a tilde (`e.~g.`, `i.~e.`). German abbreviation profiles are not introduced. Findings attach to the start of the abbreviation, enabling same-line suppression. Comments, literal code, syntax command arguments (`\url{...}`), command names (`\eg`, `\ie`), and math mode are excluded.

### TYPO-04 support

TYPO-04 is enabled by default and detects swallowed whitespace after documented parameterless commands in text mode: `\LaTeX`, `\TeX`, `\BibTeX`, `\etal`, `\eg`, and `\ie`. When one of these commands is followed by whitespace (spaces, tabs, or newlines) without an explicit terminator (`{}`, `\`, or `~`), it is flagged. Occurrences followed immediately by punctuation (`.`, `,`, `:`, `;`, `!`, `?`, `)`, `]`, `}`, quotes, or dashes) or an explicit terminator pass. Findings attach to the command start, enabling same-line suppression. Comments, literal code, syntax arguments, and math mode are excluded.

### TYPO-05 support

TYPO-05 is enabled by default and detects single hyphens (`-`) used for numeric ranges (e.g. `10-20`, `pp. 5-10`, `pages 12-15`, `100-200`) and text negative numbers (e.g. `-5`, `-10`, `(-5)`) in text mode. It recommends en-dash `--` (e.g. `10--20`) for numeric ranges and math mode (e.g. `$-5$`) or en-dash for negative numbers. En-dashes (`--`), em-dashes (`---`), math mode minus (`$-5$`, `$x - y$`), and compound-word hyphens (`state-of-the-art`, `closed-loop`, `high-dimensional`, `COVID-19`, `ISO-9001`, `x86-64`, `10-fold`) pass. Findings attach to the hyphen character, enabling same-line suppression. Comments, literal code (`verbatim`, `lstlisting`, `minted`, `\verb`), and syntax command arguments (`\label{...}`, `\url{...}`) are excluded.

### TYPO-06 support

TYPO-06 is enabled by default and detects straight double quotation marks (`"`) and straight single quotes (`'`) used as quotation marks in text mode. It recommends standard LaTeX quotation marks (`` ``word'' ``or `\enquote{word}`) or backticks for single quotes (`` `word' ``). Apostrophes in English contractions (`don't`,`it's`) and possessives (`author's`,`students'`) pass. Escaped accent commands (`\"a`,`\"o`,`\"u`,`\'e`,`\`e`), literal code (`\verb`,`verbatim`,`lstlisting`,`minted`), math mode (such as prime`$f'(x)$`), comments, and syntax command arguments are excluded. Findings attach to the straight quotation mark, enabling same-line suppression.

### TYPO-07 support

TYPO-07 is enabled by default and enforces guidelines on emphasis and font attributes in academic writing. It detects `\underline{...}` anywhere in text mode, `\textbf{...}` used as emphasis in running prose outside tables and headings, and combinations of multiple font attributes, including nested commands (`\textbf{\textit{...}}`, `\textbf{\emph{...}}`, `\emph{\textbf{...}}`, `\underline{\emph{...}}`). It recommends `\emph{...}` for single textual emphasis. Bold formatting in table headers (`tabular`, `tabular*`, `tabularx`, `tabulary`, `longtable`), single emphasis commands (`\emph{...}`, `\textit{...}`), math mode, comments, and literal environments are permitted. Prose following a table or math environment is checked as running prose. Findings attach to the forbidden or nested command, enabling same-line suppression.

### TYPO-08 support

TYPO-08 is enabled by default and detects line-break commands (`\\`, `\newline`, `\linebreak`) used as paragraph breaks in running text mode. It recommends using an empty line in the source to start a new paragraph. Row breaks in supported tables (`tabular`, `tabular*`, `tabularx`, `tabulary`, `longtable`), multiline math environments (`align`, `gather`, `multline`, `equation`, etc.), and title or author macros (`\title`, `\author`, `\subtitle`, `\institute`, `\date`) are explicitly permitted. Comments and literal environments are excluded. Findings attach to the line-break command, enabling same-line suppression.

### TYPO-10 support

TYPO-10 is enabled by default and checks that `\ref{...}` and `\pageref{...}` commands in text mode specify the category noun of the referenced object (e.g. `Figure~\ref{fig:...}`, `Section~\ref{sec:...}`, `Table~\ref{tab:...}`). The category noun must match the referenced label's prefix (`Figure`/`Abbildung` for `fig:`, `Table`/`Tabelle` for `tab:`, `Section`/`Abschnitt` for `sec:`, `Chapter`/`Kapitel` for `ch:`/`cha:`, `page`/`Seite` for `\pageref`). Coordinated references (`Figures~\ref{...} and~\ref{...}`, `Figures~\ref{...}--\ref{...}`) and subfigure suffixes (`Figure~\ref{...}(a) and~\ref{...}(b)`) are supported. Commands with built-in categories (`\autoref`, `\eqref`, `\cref`, `\Cref`) and equation labels are excluded. Findings attach to the reference command token, enabling same-line suppression.

### TYPO-11 support

TYPO-11 is enabled by default and enforces chronological equation referencing across the document reading order (`Document.traverse()`). It detects forward references where an equation is cited via `\eqref` or `\ref` before its defining `\label` command inside a display math environment or with an `eq:` prefix. Forward references across multi-file `\input` and `\include` hierarchies are detected. Undefined equation references and non-equation floats are excluded. Findings attach to the forward reference command token, enabling same-line suppression.

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

### Release verification

Manual installation and verification in an external `uv` project is documented in [docs/latex-lint/release-verification.md](docs/latex-lint/release-verification.md).
