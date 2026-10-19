"""Rule 10: Test what matters. Judged by how many tests there are for the amount of code."""
from ...models import Result
from ...registry import rule
from ..comment_why.amount_checks import STANDS_IN_FOR_CHECKS, amount_score, describe_amount, edge_range
from ..few_dependencies import count_code_lines
from .count_tests import count_tests_in_project

from .limits import LINES_PER_TEST

@rule("RULE-10-TEST-AMOUNT", "The right number of tests for the code size", weight_multiplier=STANDS_IN_FOR_CHECKS)
def check_test_amount(project):
    lines = count_code_lines(project)

    if not lines:
        return Result.passed("no source files found")

    found, expected = count_tests_in_project(project), lines / LINES_PER_TEST

    return Result.scored(amount_score(found, expected), describe_amount("tests", found, expected, *edge_range(expected), lines))
