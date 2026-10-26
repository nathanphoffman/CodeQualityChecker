"""Reads the comments in a source file, with the code each one is about."""
from .....source_code import PYTHON
from ....rule_03_simple_first.shared.find_clever import clever_constructs
from ..Comment_Found import Comment_Found
from ..limits import PRAGMA_PREFIXES
from .line_helpers import clean_text, merge_runs, next_code
from .raw_comments import python_raw, tree_raw
from .statement_spans import statement_ends

def build_comments(source, language, raw):
    """A comment is about the whole statement under it (or the one it trails), however many lines that runs."""
    lines = source.splitlines()
    clever_lines = {line for _, line in clever_constructs(source, language)}
    ends = statement_ends(source, language)
    found = []

    for first, last, text, code_before in merge_runs(raw):
        cleaned = clean_text(text)

        if cleaned.lower().startswith(PRAGMA_PREFIXES):
            continue

        next_number, next_text = next_code(lines, last)
        start = first if code_before else next_number

        explains = any(start <= line <= ends.get(start, start) for line in clever_lines)
        found.append(Comment_Found(first, last, cleaned, code_before or next_text, explains, language))

    return found

def python_comments(source):
    return build_comments(source, PYTHON, python_raw(source))

def tree_comments(source, language):
    return build_comments(source, language, tree_raw(source, language))
