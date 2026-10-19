import re

from ...python_support.python_names import python_names
from ...source_code import NAME_GROUP, PYTHON, SUFFIX_LANGUAGE, blank_out_text, read_source
from ...tree_sitter_support.parse_tree import parse_tree
from ...tree_sitter_support.tree_walk import identifiers_in, walk

# Clever on purpose: each pattern captures a declared name, one per kind of declaration.
# `let` skips destructuring like `let Some(x)` or `let Point { x }` by refusing a name followed by "(" or "{".
NAME_PATTERNS = {
    "rust": [
        re.compile(r"\bfn\s+(?P<name>\w+)"),  # "fn" then the name
        re.compile(r"\blet\s+(?:mut\s+)?(?P<name>\w+)\b(?!\s*[({])"),  # "let", optional "mut", then the name

        re.compile(r"\b(?:const|static)\s+(?:mut\s+)?(?P<name>\w+)\s*:"),  # "const" or "static", optional "mut", a name, then ":"
        re.compile(r"\b(?:struct|enum|trait|type|union|mod)\s+(?P<name>\w+)"),  # a type keyword then the name
        re.compile(r"\bfor\s+(?P<name>\w+)\s+in\b"),  # "for", the loop variable, then "in"
    ],
    "typescript": [
        re.compile(r"\bfunction\s*\*?\s*(?P<name>\w+)"),  # "function", optional "*", then the name

        re.compile(r"\b(?:const|let|var)\s+(?P<name>\w+)"),  # a variable keyword then the name
        re.compile(r"\b(?:class|interface|type|enum)\s+(?P<name>\w+)"),  # a type keyword then the name
    ],
}

# Parameters can't be found by a pattern (types, defaults and destructuring get in the way), so the syntax tree finds them:
# node type -> the field holding the new names. Rust closures list bare names between pipes, so the whole node is read.
PARAMETER_FIELDS = {
    "rust": {"parameter": "pattern", "closure_parameters": None},
    "typescript": {"required_parameter": "pattern", "optional_parameter": "pattern", "arrow_function": "parameter"},
}

def parameter_names(source, language):
    names = []

    for node in walk(parse_tree(source, language)):
        if node.type not in PARAMETER_FIELDS[language]:
            continue

        field = PARAMETER_FIELDS[language][node.type]
        declared = node.child_by_field_name(field) if field else node
        names += identifiers_in(declared, language) if declared else []

    return names

def find_names(source, language):
    # Python isn't in NAME_PATTERNS: its parser finds names exactly, so no patterns are needed.
    if language == PYTHON:
        return python_names(source)

    text = blank_out_text(source)
    names = []

    for pattern in NAME_PATTERNS[language]:
        names += [match.group(NAME_GROUP) for match in pattern.finditer(text)]

    names += parameter_names(source, language)

    return [name for name in names if name != "_"]

def names_in_project(project):
    names = []

    for path in project.files(*SUFFIX_LANGUAGE):
        names += find_names(read_source(path), SUFFIX_LANGUAGE[path.suffix])

    return names
