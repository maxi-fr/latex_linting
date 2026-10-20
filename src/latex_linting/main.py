from collections.abc import Collection
from pathlib import Path

from latex_linting.document import (
    find_root_document,
    has_documentclass,
    load_document,
    ordered_findings,
)
from latex_linting.rules.catalogue import validate_rule_id
from latex_linting.source import Finding

__all__ = ["Finding", "check"]


def _validate_rule_collections(
    ignored_rules: Collection[str] | None,
    rule_filter: Collection[str] | None,
    enabled_rules: Collection[str] | None,
) -> None:
    """Validate all provided rule IDs across user-supplied filters."""
    for rule_collection in (ignored_rules, rule_filter, enabled_rules):
        if rule_collection is not None:
            for rule_id in rule_collection:
                validate_rule_id(rule_id)


def check(  # noqa: PLR0913 -- public check interface accepts filters, root override, and external linter toggles
    path: str | Path,
    ignored_rules: Collection[str] | None = None,
    rule_filter: Collection[str] | None = None,
    enabled_rules: Collection[str] | None = None,
    *,
    root: str | Path | None = None,
    chktex: bool = False,
    lacheck: bool = False,
) -> list[Finding]:
    """Check a LaTeX root document or specific file, applying suppressions and external linters."""
    _validate_rule_collections(ignored_rules, rule_filter, enabled_rules)

    target_path = Path(path)
    if target_path.suffix == ".bib":
        document = load_document(target_path)
        return ordered_findings(
            document,
            ignored_rules=ignored_rules,
            rule_filter=rule_filter,
            enabled_rules=enabled_rules,
            chktex=chktex,
            lacheck=lacheck,
        )

    if root is not None:
        document = load_document(root)
        return ordered_findings(
            document,
            ignored_rules=ignored_rules,
            rule_filter=rule_filter,
            enabled_rules=enabled_rules,
            chktex=chktex,
            lacheck=lacheck,
            file_filter=target_path,
        )

    if has_documentclass(target_path):
        document = load_document(path)
        return ordered_findings(
            document,
            ignored_rules=ignored_rules,
            rule_filter=rule_filter,
            enabled_rules=enabled_rules,
            chktex=chktex,
            lacheck=lacheck,
            file_filter=None,
        )

    root_path = find_root_document(target_path)
    if root_path is None or not root_path.is_file() or root_path.resolve() == target_path.resolve():
        document = load_document(path)
        file_filter = None
    else:
        document = load_document(root_path)
        file_filter = target_path

    return ordered_findings(
        document,
        ignored_rules=ignored_rules,
        rule_filter=rule_filter,
        enabled_rules=enabled_rules,
        chktex=chktex,
        lacheck=lacheck,
        file_filter=file_filter,
    )
