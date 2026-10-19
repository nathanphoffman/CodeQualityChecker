"""Rule 8: Minimize dependencies. Judged by how many direct dependencies a project has per 1296 lines of code."""
from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from ...source_code import SUFFIX_LANGUAGE, non_test_files, read_source
from .limits import LINES_PER_DEPENDENCY, SCORE_PER_DEPENDENCY
from .read_manifests import project_dependencies


def count_code_lines(project):
    """Non-blank lines in the project's own (non-test) source files."""
    lines = 0
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        lines += len([line for line in read_source(path).splitlines() if line.strip()])
    return lines


@rule("RULE-08-DEPENDENCIES", "Few dependencies for the amount of code")
def check_dependencies(project):
    names = sorted(name for _, name in project_dependencies(project))
    if not names:
        return Result.passed("no dependencies")
    # A small project is judged as if it had a full 1296 lines, so one sensible dependency isn't punished.
    lines = max(count_code_lines(project), LINES_PER_DEPENDENCY)
    per_unit = len(names) * LINES_PER_DEPENDENCY / lines
    listed = ", ".join(names[:MAX_LISTED_OFFENDERS])
    message = f"{len(names)} dependencies, {per_unit:.2f} per {LINES_PER_DEPENDENCY} lines: {listed}"
    return Result.scored(SCORE_PER_DEPENDENCY ** per_unit, message)
