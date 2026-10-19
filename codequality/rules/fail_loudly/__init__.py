"""Rule 11: Fail loudly. Errors that are caught must be reported, and error checks should be neither rare nor constant."""
from ...models import MAX_LISTED_OFFENDERS, SEVERITY_ERROR, Result
from ...registry import rule
from ...source_code import items_in_project
from ..comment_why.amount_checks import amount_score, describe_amount
from ..comment_why.limits import POWER_BASE

from ..few_dependencies import count_code_lines
from .hiding_constructs import hiding_constructs
from .limits import (FULL_CREDIT_POWERS, LINES_PER_ERROR_CHECK, MAX_LINES_PER_ERROR_CHECK, MIN_LINES_PER_ERROR_CHECK,
                     NARROW_SILENT_WEIGHT)

from .python_handlers import python_handlers
from .tree_handlers import tree_handlers

def silent_cost(handler):
    """How badly a silent handler counts: 1 for one that catches anything, less for one that catches a single kind."""

    return 1.0 if handler.is_broad else NARROW_SILENT_WEIGHT

@rule("RULE-11-LOUD-ERRORS", "Caught errors are reported, not swallowed", severity=SEVERITY_ERROR)
def check_loud_errors(project):
    handlers = [(label, handler) for label, handler in items_in_project(project, python_handlers, tree_handlers) if handler.is_catch]
    hidden = hiding_constructs(project)
    total = len(handlers) + len(hidden)

    if not total:
        return Result.passed("no error handling found")

    silent = [(label, handler.line_number, silent_cost(handler)) for label, handler in handlers if not handler.is_loud]
    silent += [(label, line, 1.0) for label, line in hidden]
    listed = ", ".join(f"{label}:{line}" for label, line, _ in silent[:MAX_LISTED_OFFENDERS])
    message = f"{len(silent)} of {total} error handlers or error-hiding calls swallow errors: {listed}" if silent else ""

    return Result.scored(1 - sum(cost for _, _, cost in silent) / total, message)

@rule("RULE-11-ERROR-CHECK-AMOUNT", "The right amount of error checking for the code size")
def check_error_check_amount(project):
    lines = count_code_lines(project)
    found = len(items_in_project(project, python_handlers, tree_handlers))
    expected = lines / LINES_PER_ERROR_CHECK
    message = describe_amount("error checks", found, expected, lines / MAX_LINES_PER_ERROR_CHECK, lines / MIN_LINES_PER_ERROR_CHECK, lines)

    if not lines or (not found and lines <= MAX_LINES_PER_ERROR_CHECK):
        return Result.passed(message)  # too small a project to expect any

    return Result.scored(amount_score(found, expected, FULL_CREDIT_POWERS), message)
