from latex_linting.rules.cite_04 import RULE as CITE_04
from latex_linting.rules.math_01 import RULE as MATH_01
from latex_linting.rules.math_04 import RULE as MATH_04
from latex_linting.rules.math_13 import RULE as MATH_13
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_02 import RULE as PROSE_02
from latex_linting.rules.prose_03 import RULE as PROSE_03
from latex_linting.rules.prose_04 import RULE as PROSE_04
from latex_linting.rules.prose_07 import RULE as PROSE_07
from latex_linting.rules.struc_02 import RULE as STRUC_02
from latex_linting.rules.struc_03 import RULE as STRUC_03
from latex_linting.rules.struc_06 import RULE as STRUC_06
from latex_linting.rules.work_03 import RULE as WORK_03

RULES = (
    CITE_04,
    MATH_01,
    MATH_04,
    MATH_13,
    PROSE_02,
    PROSE_03,
    PROSE_04,
    PROSE_07,
    STRUC_02,
    STRUC_03,
    STRUC_06,
    WORK_03,
)


def get_rule(rule_id: str) -> Rule:
    """Look up an explicitly registered rule, raising KeyError for an unknown ID."""
    for rule in RULES:
        if rule.rule_id == rule_id:
            return rule
    raise KeyError(rule_id)


def validate_rule_id(rule_id: str) -> str:
    """Ensure a rule ID exists in the catalogue, raising ValueError if unknown."""
    for rule in RULES:
        if rule.rule_id == rule_id:
            return rule_id
    msg = f"unknown rule ID: {rule_id}"
    raise ValueError(msg)
