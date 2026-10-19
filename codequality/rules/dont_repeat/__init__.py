"""Rule 6: Don't repeat yourself. Finds copy-pasted functions and blocks, even when variables were renamed."""
from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from .find_duplicates import repeated_blocks, repeated_functions, shapes_in_project

def where(label, first_line):
    return f"{label}:{first_line}"

@rule("RULE-06-DUPLICATE-FUNCTIONS", "No function is a copy of another")
def check_duplicate_functions(project):
    entries = shapes_in_project(project)
    copies = repeated_functions(entries)

    if not entries:
        return Result.passed("no functions found")

    listed = ", ".join(f"{where(c[0], c[1].line_number)} {c[1].name} (same as {where(o[0], o[1].line_number)})"
                       for c, o in copies[:MAX_LISTED_OFFENDERS])

    message = f"{len(copies)} of {len(entries)} functions copy another: {listed}" if copies else ""

    return Result.scored(1 - len(copies) / len(entries), message)

def lines_of(label, run):
    return {(label, line) for statement in run for line in range(statement.first_line, statement.last_line + 1)}

@rule("RULE-06-DUPLICATE-BLOCKS", "No run of statements is copied elsewhere")
def check_duplicate_blocks(project):
    entries = shapes_in_project(project)
    copied_functions = {(c[0], c[1].line_number) for c, _ in repeated_functions(entries)}
    judged = [entry for entry in entries if (entry[0], entry[1].line_number) not in copied_functions]
    all_lines = set()

    for label, function in judged:
        for sequence in function.sequences:
            all_lines |= lines_of(label, sequence)

    if not all_lines:
        return Result.passed("no statements found")

    repeats = repeated_blocks(judged)

    repeated_lines = set()

    for label, run, _, _ in repeats:
        repeated_lines |= lines_of(label, run)

    listed = ", ".join(f"{where(label, run[0].first_line)}-{run[-1].last_line} (same as {where(original, first[0].first_line)})"
                       for label, run, original, first in repeats[:MAX_LISTED_OFFENDERS])

    message = f"{len(repeated_lines)} of {len(all_lines)} lines are repeats: {listed}" if repeats else ""

    return Result.scored(1 - len(repeated_lines) / len(all_lines), message)
