"""Rule 10: Test what matters. Judged by how many tests there are for the amount of code."""
from ...models import Result
from ...registry import rule
from ..comment_why.shared.amount_checks import STANDS_IN_FOR_CHECKS, amount_score, describe_amount, edge_range
from ..few_dependencies import count_code_lines
from .count_tests import count_tests_in_project

from .limits import LINES_PER_TEST, MAX_LINES_WITHOUT_TESTS

@rule("RULE-10-TEST-AMOUNT", "The right number of tests for the code size", weight_multiplier=STANDS_IN_FOR_CHECKS)
def check_test_amount(project):
    lines = count_code_lines(project)

    if not lines:
        return Result.passed("no source files found")

    # A small project is judged as if it had MAX_LINES_WITHOUT_TESTS lines, so one or two tests are never too many.
    found, expected = count_tests_in_project(project), max(lines, MAX_LINES_WITHOUT_TESTS) / LINES_PER_TEST

    if not found and lines < MAX_LINES_WITHOUT_TESTS:
        return Result.passed(f"{lines} lines of code is under {MAX_LINES_WITHOUT_TESTS}, too small to need tests")

    return Result.scored(amount_score(found, expected), describe_amount("tests", found, expected, *edge_range(expected), lines))
