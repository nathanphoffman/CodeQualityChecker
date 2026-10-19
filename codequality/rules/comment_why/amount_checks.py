"""How many comments there are, whatever they say: about one per 15 lines is ideal, and being far off in either direction costs a lot."""
import math

from ...models import Result
from ...registry import rule
from ...source_code import items_in_project
from ..few_dependencies import count_code_lines
from .extract import python_comments, tree_comments
from .limits import EDGE_DISTANCE, EDGE_SCORE, FALLOFF_PER_STEP, LINES_PER_COMMENT, POWER_BASE

# This one rule is a too-few check and a too-many check in one, so it counts twice as much as an ordinary warning.
STANDS_IN_FOR_CHECKS = 2


def amount_score(found, expected):
    """A peak: 100% when found equals expected, EDGE_SCORE at EDGE_DISTANCE powers of 6 off, then falling fast."""
    if not found:
        return 0.0
    steps = abs(math.log(found / expected, POWER_BASE)) / EDGE_DISTANCE
    if steps <= 1:
        return 1 - (1 - EDGE_SCORE) * steps
    return EDGE_SCORE * FALLOFF_PER_STEP ** (steps - 1)


def describe_amount(noun, found, expected, lines):
    """`Encountered 103 comments, expected 149 (range 61 to 365, 2185 lines of code)`. The range is where EDGE_SCORE applies."""
    spread = POWER_BASE ** EDGE_DISTANCE
    return f"Encountered {found} {noun}, expected {expected:.0f} (range {expected / spread:.0f} to {expected * spread:.0f}, {lines} lines of code)"


def count_plain_comments(project):
    """Comments on clever code are left out: rule 3 asks for those, so they say nothing about how much commentary there is."""
    comments = [comment for _, comment in items_in_project(project, python_comments, tree_comments)]
    return len([comment for comment in comments if not comment.explains_clever])


@rule("RULE-09-COMMENT-AMOUNT", "The right amount of comments for the code size", weight_multiplier=STANDS_IN_FOR_CHECKS)
def check_comment_amount(project):
    lines = count_code_lines(project)
    if not lines:
        return Result.passed("no source files found")
    found, expected = count_plain_comments(project), lines / LINES_PER_COMMENT
    return Result.scored(amount_score(found, expected), describe_amount("non-complex comments", found, expected, lines))
