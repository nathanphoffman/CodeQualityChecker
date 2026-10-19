"""Finds the calls and other constructs rule 5 looks at, in Python, Rust and TypeScript files."""
from ....source_code import SUFFIX_LANGUAGE
from .python_uses import python_uses
from .tree_uses import tree_uses

# Tests may fake secrets and call unsafe things on purpose, so rule 5 only judges real code.
TEST_FOLDERS = {"tests", "test", "__tests__", "fixtures"}


def find_uses(source, language):
    return python_uses(source) if language == "python" else tree_uses(source, language)


def scannable_files(project, suffixes):
    """Project files with these suffixes, outside test folders."""
    return [path for path in project.files(*suffixes) if not TEST_FOLDERS & set(path.relative_to(project.root).parts)]


def uses_in_project(project):
    """(file label, language, uses) for every Python, Rust and TypeScript file."""
    found = []
    for path in scannable_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        found.append((project.label_for(path), language, find_uses(path.read_text(errors="ignore"), language)))
    return found
