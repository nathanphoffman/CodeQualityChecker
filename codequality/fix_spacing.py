import warnings

from .rules.rule_14_space_out import file_gaps
from .rules.rule_14_space_out.shared.limits import MAX_BLANK_LINES_IN_A_ROW
from .rules.rule_14_space_out.shared.paragraphs import find_blank_runs
from .source_code import PYTHON, SUFFIX_LANGUAGE, read_source

def collapse_blank_lines(lines, language, source):
    """The lines with every stretch of blank lines cut down to the allowed length. Python is left alone, as PEP 8 wants two."""
    dropped = set()

    for first, length in find_blank_runs(lines) if language != PYTHON else []:
        dropped |= set(range(first + MAX_BLANK_LINES_IN_A_ROW, first + length))

    return [line for number, line in enumerate(lines, start=1) if number not in dropped]

def fix_source(source, language):
    """The source with doubled blank lines removed and a blank line added above every place the spacing rule wants one."""
    lines = collapse_blank_lines(source.splitlines(), language, source)
    collapsed = "\n".join(lines) + "\n"
    gaps = file_gaps(language, collapsed)
    missing = set(gaps.before_control_missing) | set(gaps.after_block_missing)
    fixed = []

    for number, line in enumerate(lines, start=1):
        fixed += [""] if number in missing else []
        fixed.append(line)

    return "\n".join(fixed) + "\n"

def fix_spacing(project):
    """Rewrites files in place. Returns the labels of the files that changed. A file that can't be parsed is left alone."""
    changed = []

    for path in project.files(*SUFFIX_LANGUAGE):
        source = read_source(path)

        try:
            fixed = fix_source(source, SUFFIX_LANGUAGE[path.suffix]) if source else source
        except (SyntaxError, ValueError) as error:
            warnings.warn(f"left {path} alone, it could not be read: {error}")  # rewriting a file we cannot parse could break it

            continue

        if fixed != source:
            path.write_text(fixed)
            changed.append(project.label_for(path))

    return changed
