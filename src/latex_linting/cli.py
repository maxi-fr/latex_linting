import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from latex_linting.document import MissingIncludeError
from latex_linting.main import check
from latex_linting.refs import (
    extract_citations_from_project,
    extract_reference_texts,
    fetch_missing_references,
    load_bib_entries_from_project,
)
from latex_linting.rules.catalogue import get_rule
from latex_linting.skills_install import install_skills, resolve_install_destination


def _handle_install_skills(args: argparse.Namespace) -> int:
    """Handle the install-skills subcommand."""
    try:
        destination = resolve_install_destination(args.preset, args.dest)
        installed = install_skills(destination, force=args.force)
    except (ValueError, FileExistsError, OSError) as error:
        sys.stderr.write(f"latex-lint: {error}\n")
        return 2
    for path in installed:
        sys.stdout.write(f"Installed {path.name} to {path}\n")
    return 0


def _handle_rule(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Handle the rule subcommand."""
    try:
        rule = get_rule(args.rule_id)
    except KeyError:
        parser.error(f"unknown rule ID: {args.rule_id}")
    sys.stdout.write(
        f"{rule.rule_id}: {rule.explanation}\n{rule.correction}\n\n"
        "Passing examples:\n" + "\n".join(rule.passing_examples) + "\n\n"
        "Failing examples:\n" + "\n".join(rule.failing_examples) + "\n\n"
        f"Detection limits:\n{rule.limits}\n"
    )
    return 0


def _handle_check(args: argparse.Namespace) -> int:
    """Handle the check subcommand."""
    ignored_rules = [part.strip() for part in args.ignore.split(",")] if args.ignore is not None else None
    rule_filter = [part.strip() for part in args.rule.split(",")] if args.rule is not None else None
    enabled_rules = [part.strip() for part in args.enable.split(",")] if args.enable is not None else None
    try:
        findings = check(
            args.root,
            ignored_rules=ignored_rules,
            rule_filter=rule_filter,
            enabled_rules=enabled_rules,
        )
    except MissingIncludeError as error:
        sys.stderr.write(f"latex-lint: {error}\n")
        return 2
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"latex-lint: {args.root}: {error}\n")
        return 2
    except ValueError as error:
        sys.stderr.write(f"latex-lint: {error}\n")
        return 2
    for finding in findings:
        sys.stdout.write(
            f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id} {finding.explanation}\n"
            f"  {finding.excerpt}\n  Suggestion: {finding.correction}\n"
        )
    return int(bool(findings))


def _handle_refs_fetch(args: argparse.Namespace) -> int:
    """Handle the refs fetch subcommand."""
    root = Path(args.root)
    base_dir = root.parent if root.is_file() else root
    refs_dir = args.references_dir if args.references_dir.is_absolute() else base_dir / args.references_dir
    try:
        citations = extract_citations_from_project(root)
        bib_entries = load_bib_entries_from_project(root, args.bib)
        result = fetch_missing_references(citations, bib_entries, refs_dir, force=args.force)
    except (OSError, UnicodeError, ValueError) as error:
        sys.stderr.write(f"latex-lint: {error}\n")
        return 2

    sys.stdout.write(f"Existing references: {len(result.existing)}\n")
    sys.stdout.write(f"Downloaded references: {len(result.downloaded)}\n")
    for key, path in result.downloaded:
        sys.stdout.write(f"  + {key} -> {path}\n")

    if result.unretrieved:
        sys.stdout.write(f"\nUnresolved references ({len(result.unretrieved)}):\n")
        sys.stdout.write("| Key | Title | DOI / URL |\n")
        sys.stdout.write("| --- | ----- | --------- |\n")
        for item in result.unretrieved:
            loc = item.doi or item.url or "N/A"
            sys.stdout.write(f"| {item.key} | {item.title} | {loc} |\n")
        sys.stdout.write(f"\nPlease manually place missing PDFs into '{refs_dir}/<citekey>.pdf' before verifying.\n")
        return 1
    return 0


def _handle_refs_extract(args: argparse.Namespace) -> int:
    """Handle the refs extract subcommand."""
    root = Path(args.root)
    base_dir = root.parent if root.is_file() else root
    refs_dir = (
        args.references_dir
        if (args.references_dir and args.references_dir.is_absolute())
        else base_dir / (args.references_dir or "references")
    )
    out_dir = (
        args.output_dir
        if (args.output_dir and args.output_dir.is_absolute())
        else base_dir / (args.output_dir or Path(".latex_lint") / "references_text")
    )

    if not refs_dir.exists():
        sys.stderr.write(f"latex-lint: references directory '{refs_dir}' does not exist\n")
        return 2

    try:
        extracted = extract_reference_texts(refs_dir, out_dir, force=args.force)
    except (OSError, UnicodeError, ValueError) as error:
        sys.stderr.write(f"latex-lint: {error}\n")
        return 2

    sys.stdout.write(f"Extracted text for {len(extracted)} reference(s) to {out_dir}\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch CLI operations, returning 0, 1, or 2."""
    parser = argparse.ArgumentParser(prog="latex-lint", description="Check LaTeX thesis source conventions.")
    operations = parser.add_subparsers(dest="operation", required=True)
    check_parser = operations.add_parser(
        "check",
        help="check an explicit UTF-8 root document (<root> [--ignore RULES])",
        description="Check an explicit UTF-8 root document and all included files.",
        epilog=(
            "in-source rule suppression:\n"
            "  Use LaTeX comments to suppress rules directly in the document:\n"
            "    % latex-lint:ignore=RULE-ID       suppress on this line only\n"
            "    % latex-lint:disable=RULE-ID      disable from this point onward\n"
            "    % latex-lint:enable=RULE-ID       re-enable previously disabled rule\n"
            "  Multiple comma-separated rule IDs are supported (e.g. % latex-lint:ignore=MATH-04,PROSE-02)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check_parser.add_argument("root", help="path to root .tex or .bib document")
    check_parser.add_argument("--ignore", default=None, help="comma-separated rule IDs to ignore across the invocation")
    check_parser.add_argument("--rule", default=None, help="comma-separated rule IDs to run exclusively")
    check_parser.add_argument("--enable", default=None, help="comma-separated off-by-default rule IDs to enable")
    rule_parser = operations.add_parser(
        "rule",
        help="show an implemented rule and examples (<rule_id>)",
    )
    rule_parser.add_argument("rule_id", help="rule identifier to inspect (e.g. MATH-04)")
    install_parser = operations.add_parser(
        "install-skills",
        help="install bundled agent skills ([preset] [-d/--dest PATH] [-f/--force])",
    )
    install_parser.add_argument(
        "preset",
        nargs="?",
        choices=["local", "global", "claude", "claude-global"],
        default=None,
        help="predefined target directory (local, global, claude, claude-global; default: local)",
    )
    install_parser.add_argument(
        "--dest",
        "-d",
        type=Path,
        default=None,
        help="custom destination directory path",
    )
    install_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="overwrite existing skill directories if they already exist",
    )

    refs_parser = operations.add_parser(
        "refs",
        help="manage reference papers and text extraction (fetch, extract)",
    )
    refs_sub = refs_parser.add_subparsers(dest="refs_action", required=True)

    fetch_parser = refs_sub.add_parser("fetch", help="fetch missing reference PDFs into references/")
    fetch_parser.add_argument("root", nargs="?", default=".", help="project root or document path (default: .)")
    fetch_parser.add_argument(
        "--references-dir",
        "-r",
        type=Path,
        default=Path("references"),
        help="destination directory for reference PDFs (default: references)",
    )
    fetch_parser.add_argument("--bib", "-b", type=Path, default=None, help="explicit path to .bib file")
    fetch_parser.add_argument("--force", "-f", action="store_true", help="re-download existing reference PDFs")

    extract_parser = refs_sub.add_parser("extract", help="extract page-annotated text from reference PDFs")
    extract_parser.add_argument("root", nargs="?", default=".", help="project root or document path (default: .)")
    extract_parser.add_argument(
        "--references-dir",
        "-r",
        type=Path,
        default=None,
        help="references directory containing PDFs (default: references)",
    )
    extract_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="output directory for extracted text (default: .latex_lint/references_text)",
    )
    extract_parser.add_argument("--force", "-f", action="store_true", help="re-extract even if text file exists")

    args = parser.parse_args(argv)
    if args.operation == "install-skills":
        return _handle_install_skills(args)
    if args.operation == "rule":
        return _handle_rule(args, parser)
    if args.operation == "refs":
        if args.refs_action == "fetch":
            return _handle_refs_fetch(args)
        if args.refs_action == "extract":
            return _handle_refs_extract(args)
    return _handle_check(args)
