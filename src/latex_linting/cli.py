import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from latex_linting.document import MissingIncludeError
from latex_linting.main import check
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
    try:
        findings = check(args.root, ignored_rules=ignored_rules)
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


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch CLI operations, returning 0, 1, or 2."""
    parser = argparse.ArgumentParser(prog="latex-lint", description="Check LaTeX thesis source conventions.")
    operations = parser.add_subparsers(dest="operation", required=True)
    check_parser = operations.add_parser(
        "check",
        help="check an explicit UTF-8 root document (<root> [--ignore RULES])",
    )
    check_parser.add_argument("root", help="path to root .tex or .bib document")
    check_parser.add_argument("--ignore", default=None, help="comma-separated rule IDs to ignore across the invocation")
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
    args = parser.parse_args(argv)
    if args.operation == "install-skills":
        return _handle_install_skills(args)
    if args.operation == "rule":
        return _handle_rule(args, parser)
    return _handle_check(args)
