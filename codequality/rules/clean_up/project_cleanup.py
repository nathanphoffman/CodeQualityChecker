from collections import Counter

from ...source_code import PYTHON, SUFFIX_LANGUAGE, read_source
from .python_checks import analyze_python
from .tree_checks import analyze_tree

PACKAGE_INIT = "__init__.py"

def analyze_project(project):
    """[(file label, Cleanup_Findings, Name_Usage)] for every Python, Rust and TypeScript file, tests included."""
    analyzed = []

    for path in project.files(*SUFFIX_LANGUAGE):
        language, source = SUFFIX_LANGUAGE[path.suffix], read_source(path)
        found = analyze_python(source, path.name == PACKAGE_INIT) if language == PYTHON else analyze_tree(source, language)
        analyzed.append((project.label_for(path), *found))

    return analyzed

def unused_private_definitions(analyzed):
    """[(file label, line number, name)] for private definitions whose name is never mentioned anywhere else in the project."""
    mentions = Counter()
    definitions = Counter()

    for _, _, usage in analyzed:
        mentions.update(usage.references)
        definitions.update(name for name, _ in usage.private_definitions)

    return [(label, line, name) for label, _, usage in analyzed for name, line in usage.private_definitions
            if mentions[name] <= definitions[name]]
