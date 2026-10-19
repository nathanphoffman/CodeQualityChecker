"""Rule 14: Space it out. Blank lines separate ideas like paragraphs, so code paragraphs stay short and blank runs stay small."""
from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from ...source_code import SUFFIX_LANGUAGE, read_source
from ..power_of_six.limits import MAX_ITEMS
from ..power_of_six.scoring import function_length_credit
from .limits import MAX_BLANK_LINES_IN_A_ROW
from .paragraphs import find_blank_runs, find_paragraphs, is_judged


def source_lines_by_file(project):
    """{file label: lines} for every Python, Rust and TypeScript file, tests included."""
    return {project.label_for(path): read_source(path).splitlines() for path in project.files(*SUFFIX_LANGUAGE)}


@rule("RULE-14-SHORT-PARAGRAPHS", "Code is broken into short paragraphs")
def check_short_paragraphs(project):
    judged = [(label, first, length) for label, lines in source_lines_by_file(project).items()
              for first, length in find_paragraphs(lines) if is_judged(lines, first, length)]
    if not judged:
        return Result.passed("no code found")
    long_ones = sorted((entry for entry in judged if entry[2] > MAX_ITEMS), key=lambda entry: entry[2], reverse=True)
    listed = ", ".join(f"{label}:{first} ({length})" for label, first, length in long_ones[:MAX_LISTED_OFFENDERS])
    message = f"{len(long_ones)} of {len(judged)} paragraphs run over {MAX_ITEMS} lines: {listed}" if long_ones else ""
    return Result.scored(sum(function_length_credit(length) for _, _, length in judged) / len(judged), message)


@rule("RULE-14-BLANK-LINES-IN-MODERATION", "No long stretches of blank lines")
def check_blank_lines(project):
    runs = [(label, first, length) for label, lines in source_lines_by_file(project).items() for first, length in find_blank_runs(lines)]
    if not runs:
        return Result.passed("no blank lines found")
    too_long = [(label, first, length) for label, first, length in runs if length > MAX_BLANK_LINES_IN_A_ROW]
    listed = ", ".join(f"{label}:{first} ({length} blank lines)" for label, first, length in too_long[:MAX_LISTED_OFFENDERS])
    message = f"{len(too_long)} of {len(runs)} blank stretches are longer than {MAX_BLANK_LINES_IN_A_ROW}: {listed}" if too_long else ""
    return Result.scored(1 - len(too_long) / len(runs), message)
