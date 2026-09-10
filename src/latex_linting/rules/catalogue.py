from latex_linting.rules.math_04 import RULE as MATH_04
from latex_linting.rules.model import Rule

RULES = (MATH_04,)


def get_rule(rule_id: str) -> Rule:
    """Look up an explicitly registered rule, raising KeyError for an unknown ID."""
    for rule in RULES:
        if rule.rule_id == rule_id:
            return rule
    raise KeyError(rule_id)
