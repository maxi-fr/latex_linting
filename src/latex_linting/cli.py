import argparse
import sys
from collections.abc import Sequence

from latex_linting.main import check
from latex_linting.rules.catalogue import get_rule


def main(argv: Sequence[str] | None = None) -> int:
    """Run check or rule help, returning 0 for success, 1 for findings, or 2 for input errors."""
    parser = argparse.ArgumentParser(prog="latex-lint", description="Check LaTeX thesis source conventions.")
    operations = parser.add_subparsers(dest="operation", required=True)
    check_parser = operations.add_parser("check", help="check an explicit UTF-8 root document")
    check_parser.add_argument("root")
    rule_parser = operations.add_parser("rule", help="show an implemented rule and examples")
    rule_parser.add_argument("rule_id")
    args = parser.parse_args(argv)
    if args.operation == "rule":
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
    try:
        findings = check(args.root)
    except (OSError, UnicodeError) as error:
        sys.stderr.write(f"latex-lint: {args.root}: {error}\n")
        return 2
    for finding in findings:
        sys.stdout.write(
            f"{finding.filename}:{finding.line}:{finding.column}: {finding.rule_id} {finding.explanation}\n"
            f"  {finding.excerpt}\n  Suggestion: {finding.correction}\n"
        )
    return int(bool(findings))
