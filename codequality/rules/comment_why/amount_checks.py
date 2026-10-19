"""How many comments there are, whatever they say: about one per 36 lines is right, too few is worse than too many."""
from ...models import Result
from ...registry import rule
from ...source_code import items_in_project
from ..few_dependencies import count_code_lines
from .extract import python_comments, tree_comments
from .limits import LINES_PER_COMMENT, TOO_FEW_EXPONENT, TOO_MANY_EXPONENT


def comments_per_target(project):
    """(comment count, line count, comments per LINES_PER_COMMENT lines). 1.0 is the target."""
    # Comments on clever code are left out: rule 3 asks for those, so they say nothing about how much commentary there is.
    comments = [comment for _, comment in items_in_project(project, python_comments, tree_comments)]
    count = len([comment for comment in comments if not comment.explains_clever])
    lines = count_code_lines(project)
    return count, lines, count * LINES_PER_COMMENT / lines if lines else 0.0


def describe(count, lines, density):
    return f"{count} comments in {lines} lines, {density:.2f} per {LINES_PER_COMMENT} lines (the target is 1.00)"


@rule("RULE-09-ENOUGH-COMMENTS", "Enough comments")
def check_enough_comments(project):
    count, lines, density = comments_per_target(project)
    if not lines:
        return Result.passed("no source files found")
    return Result.scored(min(1.0, density) ** TOO_FEW_EXPONENT, describe(count, lines, density))


@rule("RULE-09-MODEST-COMMENTS", "A modest number of comments")
def check_not_too_many_comments(project):
    count, lines, density = comments_per_target(project)
    if not lines or density <= 1.0:
        return Result.passed(describe(count, lines, density) if lines else "no source files found")
    return Result.scored((1 / density) ** TOO_MANY_EXPONENT, describe(count, lines, density))
