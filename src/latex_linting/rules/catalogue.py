from latex_linting.rules.cite_04 import RULE as CITE_04
from latex_linting.rules.cite_08 import RULE as CITE_08
from latex_linting.rules.fig_03 import RULE as FIG_03
from latex_linting.rules.fig_06 import RULE as FIG_06
from latex_linting.rules.fig_07 import RULE as FIG_07
from latex_linting.rules.fig_08 import RULE as FIG_08
from latex_linting.rules.math_01 import RULE as MATH_01
from latex_linting.rules.math_02 import RULE as MATH_02
from latex_linting.rules.math_03 import RULE as MATH_03
from latex_linting.rules.math_04 import RULE as MATH_04
from latex_linting.rules.math_06 import RULE as MATH_06
from latex_linting.rules.math_09 import RULE as MATH_09
from latex_linting.rules.math_12 import RULE as MATH_12
from latex_linting.rules.math_13 import RULE as MATH_13
from latex_linting.rules.math_14 import RULE as MATH_14
from latex_linting.rules.model import Rule
from latex_linting.rules.prose_02 import RULE as PROSE_02
from latex_linting.rules.prose_03 import RULE as PROSE_03
from latex_linting.rules.prose_04 import RULE as PROSE_04
from latex_linting.rules.prose_07 import RULE as PROSE_07
from latex_linting.rules.struc_02 import RULE as STRUC_02
from latex_linting.rules.struc_03 import RULE as STRUC_03
from latex_linting.rules.struc_06 import RULE as STRUC_06
from latex_linting.rules.tab_01 import RULE as TAB_01
from latex_linting.rules.tab_02 import RULE as TAB_02
from latex_linting.rules.tab_03 import RULE as TAB_03
from latex_linting.rules.typo_01 import RULE as TYPO_01
from latex_linting.rules.typo_02 import RULE as TYPO_02
from latex_linting.rules.typo_03 import RULE as TYPO_03
from latex_linting.rules.typo_04 import RULE as TYPO_04
from latex_linting.rules.typo_05 import RULE as TYPO_05
from latex_linting.rules.typo_06 import RULE as TYPO_06
from latex_linting.rules.typo_07 import RULE as TYPO_07
from latex_linting.rules.typo_08 import RULE as TYPO_08
from latex_linting.rules.typo_09 import RULE as TYPO_09
from latex_linting.rules.work_03 import RULE as WORK_03

RULES = (
    CITE_04,
    CITE_08,
    FIG_03,
    FIG_06,
    FIG_07,
    FIG_08,
    MATH_01,
    MATH_02,
    MATH_03,
    MATH_04,
    MATH_06,
    MATH_09,
    MATH_12,
    MATH_13,
    MATH_14,
    PROSE_02,
    PROSE_03,
    PROSE_04,
    PROSE_07,
    STRUC_02,
    STRUC_03,
    STRUC_06,
    TAB_01,
    TAB_02,
    TAB_03,
    TYPO_01,
    TYPO_02,
    TYPO_03,
    TYPO_04,
    TYPO_05,
    TYPO_06,
    TYPO_07,
    TYPO_08,
    TYPO_09,
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
