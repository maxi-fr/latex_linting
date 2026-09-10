# latex-linting

Linting plus review agents for thesis writing

## Check a document

Requires Python 3.13 or later. From this checkout:

```bash
uv sync
uv run latex-lint check path/to/thesis.tex
uv run latex-lint rule MATH-04
```

Installing this package also installs the `latex-lint` command. The root document
is required and must be UTF-8. The checker reads only that file in this version;
it does not follow `\input` or `\include` yet. It never changes source files,
compiles TeX, or expands macros.

Exit codes are `0` for a clean check or successful rule help, `1` for findings,
and `2` for input errors such as unreadable files, invalid UTF-8, missing arguments,
or unknown rule IDs. Findings go to stdout; input errors go to stderr.
This is a style checker, not a LaTeX syntax validator.

### Python interface

```python
from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule

findings = check("path/to/thesis.tex")
rule = get_rule("MATH-04")
```

`check` accepts a string or `pathlib.Path` and returns a list of immutable `Finding`
objects without printing. Each has `rule_id`, `filename`, `line`, `column`,
`excerpt`, `explanation`, and `correction` fields. The filename retains the supplied
path. Lines and columns are one-based; columns count Unicode characters, with a tab
counting as one character. The excerpt is the original line without its line ending.
Findings are ordered by line, column, then rule ID. File and decoding errors propagate
as `OSError` and `UnicodeError`. `get_rule` raises `KeyError` for an unknown ID.

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
