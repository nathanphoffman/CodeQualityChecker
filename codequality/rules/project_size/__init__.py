"""Rule 13: Keep the project small. The total line count, in powers of 6, should stay at 6 ** 6 lines or below."""
import math

from ...models import Result
from ...registry import rule
from ...source_code import SUFFIX_LANGUAGE, read_source
from .limits import BASE, DECAY, EDGE_POWER, FULL_CREDIT_POWER, SCORE_AT_EDGE, STEEPNESS


def count_project_lines(project):
    """Non-blank lines in every Python, Rust and TypeScript file, tests included: the size of the whole project."""
    lines = 0
    for path in project.files(*SUFFIX_LANGUAGE):
        lines += len([line for line in read_source(path).splitlines() if line.strip()])
    return lines


def size_score(power):
    """100% up to FULL_CREDIT_POWER, a gentle slope down to SCORE_AT_EDGE at EDGE_POWER, then a steepening fall."""
    if power <= FULL_CREDIT_POWER:
        return 1.0
    if power <= EDGE_POWER:
        return 1 - (1 - SCORE_AT_EDGE) * ((power - FULL_CREDIT_POWER) / (EDGE_POWER - FULL_CREDIT_POWER)) ** 2

    return SCORE_AT_EDGE * math.exp(-DECAY * (power - EDGE_POWER) ** STEEPNESS)


@rule("RULE-13-PROJECT-SIZE", "The project stays small")
def check_project_size(project):
    lines = count_project_lines(project)
    if not lines:
        return Result.passed("no source files found")
    power = math.log(lines, BASE)

    message = f"{lines:,} lines of code, 6^{power:.1f} (full marks to {BASE ** FULL_CREDIT_POWER:,}, {SCORE_AT_EDGE:.0%} at {BASE ** EDGE_POWER:,})"
    return Result.scored(size_score(power), message)
