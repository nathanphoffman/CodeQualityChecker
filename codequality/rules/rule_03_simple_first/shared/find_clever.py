from ....language_parsers.deor.rust_blocks import rust_only_source
from ..python.python_clever import python_clever
from ....source_code import C_LANG, CSHARP, DEOR, PYTHON, RUST, SUFFIX_LANGUAGE, TYPESCRIPT, blank_out_text, non_test_files, read_source
from .Clever_Hit import Clever_Hit
from ..tree_sitter.clever_patterns import pattern_hits
from .find_structures import long_chain_hits, nested_closure_hits, ternary_hits
from .limits import LINE_ABOVE_COMMENTS, SAME_LINE_COMMENTS

def is_explained(lines, line_number, language):
    """A comment on the same line, or on the line right above, counts as an explanation."""

    if any(marker in lines[line_number - 1] for marker in SAME_LINE_COMMENTS[language]):
        return True

    return line_number > 1 and lines[line_number - 2].strip().startswith(LINE_ABOVE_COMMENTS[language])

def clever_constructs(source, language):
    """(kind, line_number) pairs. Python is read with its parser; Rust and TypeScript with patterns.
    Deor has no clever constructs of its own, so only what its `rust` blocks do is judged."""

    if language == PYTHON:
        return python_clever(source)

    if language == DEOR:
        return clever_constructs(rust_only_source(source), RUST)

    text = blank_out_text(source, language)
    found = pattern_hits(source, text, language) + long_chain_hits(text, language) + nested_closure_hits(text, language)

    return found + ternary_hits(text) if language in (TYPESCRIPT, C_LANG, CSHARP) else found

def find_clever(source, language, file_label):
    lines = source.splitlines() or [""]

    return [Clever_Hit(kind, f"{file_label}:{line}", is_explained(lines, line, language))
            for kind, line in clever_constructs(source, language)]

def scan_project(project):
    """Returns (all clever hits, total source lines). Test files are left out: their describe/it wrappers are not clever code."""
    hits, line_count = [], 0

    for path in non_test_files(project, SUFFIX_LANGUAGE):
        source = read_source(path)
        hits += find_clever(source, SUFFIX_LANGUAGE[path.suffix], project.label_for(path))
        line_count += source.count("\n") + 1

    return hits, line_count
