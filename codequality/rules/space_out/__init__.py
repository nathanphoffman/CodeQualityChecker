"""Rule 14: Space it out. Blank lines separate ideas like paragraphs: short paragraphs, a break before control flow and
after multi-line statements, and never two blank lines in a row."""

from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from .deor.deor_spacing import deor_gaps
from ...source_code import DEOR, PYTHON, SUFFIX_LANGUAGE, read_source
from ..power_of_six.shared.limits import MAX_ITEMS
from ..power_of_six.shared.scoring import function_length_credit
from .shared.limits import MAX_BLANK_LINES_IN_A_ROW
from .shared.Spacing_Gaps import Spacing_Gaps
from .shared.paragraphs import find_blank_runs, find_paragraphs, is_judged
from .python.python_spacing import python_gaps, python_string_lines
from .tree_sitter.text_spacing import text_gaps

def source_files(project):
    """[(file label, language, source)] for every Python, Rust and TypeScript file, tests included."""

    return [(project.label_for(path), SUFFIX_LANGUAGE[path.suffix], read_source(path)) for path in project.files(*SUFFIX_LANGUAGE)]

def grade_gaps(project, total_field, missing_field, noun):
    """Score is the share of places that have their blank line. `noun` finishes the sentence "N of M ... are missing one"."""
    total, places = 0, []

    for label, language, source in source_files(project):
        gaps = python_gaps(source) if language == PYTHON else Spacing_Gaps(*deor_gaps(source)) if language == DEOR else text_gaps(source, language)
        total += getattr(gaps, total_field)
        places += [f"{label}:{line}" for line in getattr(gaps, missing_field)]

    if not total:
        return Result.passed(f"no {noun} found")

    message = f"{len(places)} of {total} {noun} have no blank line above: {', '.join(places[:MAX_LISTED_OFFENDERS])}" if places else ""

    return Result.scored(1 - len(places) / total, message)

@rule("RULE-14-SHORT-PARAGRAPHS", "Code is broken into short paragraphs")
def check_short_paragraphs(project):
    judged = []

    for label, _, source in source_files(project):
        lines = source.splitlines()
        judged += [(label, first, length) for first, length in find_paragraphs(lines) if is_judged(lines, first, length)]

    if not judged:
        return Result.passed("no code found")

    long_ones = sorted((entry for entry in judged if entry[2] > MAX_ITEMS), key=lambda entry: entry[2], reverse=True)
    listed = ", ".join(f"{label}:{first} ({length})" for label, first, length in long_ones[:MAX_LISTED_OFFENDERS])
    message = f"{len(long_ones)} of {len(judged)} paragraphs run over {MAX_ITEMS} lines: {listed}" if long_ones else ""

    return Result.scored(sum(function_length_credit(length) for _, _, length in judged) / len(judged), message)

@rule("RULE-14-BLANK-BEFORE-CONTROL", "A blank line before control statements, returns and definitions")
def check_blank_before_control(project):
    return grade_gaps(project, "before_control_total", "before_control_missing", "control statements, returns and definitions")

@rule("RULE-14-BLANK-AFTER-BLOCKS", "A blank line after multi-line statements")
def check_blank_after_blocks(project):
    return grade_gaps(project, "after_block_total", "after_block_missing", "statements after a multi-line statement")

@rule("RULE-14-NO-DOUBLE-BLANK-LINES", "Never two blank lines in a row")
def check_blank_lines(project):
    runs = []

    for label, language, source in source_files(project):
        protected = python_string_lines(source) if language == PYTHON else frozenset()
        runs += [(label, first, length) for first, length in find_blank_runs(source.splitlines(), protected)]

    if not runs:
        return Result.passed("no blank lines found")

    too_long = [(label, first, length) for label, first, length in runs if length > MAX_BLANK_LINES_IN_A_ROW]
    listed = ", ".join(f"{label}:{first} ({length} blank lines)" for label, first, length in too_long[:MAX_LISTED_OFFENDERS])
    message = f"{len(too_long)} of {len(runs)} blank stretches are longer than {MAX_BLANK_LINES_IN_A_ROW}: {listed}" if too_long else ""

    return Result.scored(1 - len(too_long) / len(runs), message)
