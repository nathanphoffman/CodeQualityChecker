import re

from ...python_support.python_names import python_names
from ...source_code import SUFFIX_LANGUAGE, blank_out_text

# Clever on purpose: each pattern captures a declared name, one per kind of declaration.
# `let` skips destructuring like `let Some(x)` or `let Point { x }` by refusing a name followed by "(" or "{".
NAME_PATTERNS = {
    "rust": [
        re.compile(r"\bfn\s+(?P<name>\w+)"),
        re.compile(r"\blet\s+(?:mut\s+)?(?P<name>\w+)\b(?!\s*[({])"),
        re.compile(r"\b(?:const|static)\s+(?:mut\s+)?(?P<name>\w+)\s*:"),
        re.compile(r"\b(?:struct|enum|trait|type|union|mod)\s+(?P<name>\w+)"),
        re.compile(r"\bfor\s+(?P<name>\w+)\s+in\b"),
    ],
    "typescript": [
        re.compile(r"\bfunction\s*\*?\s*(?P<name>\w+)"),
        re.compile(r"\b(?:const|let|var)\s+(?P<name>\w+)"),
        re.compile(r"\b(?:class|interface|type|enum)\s+(?P<name>\w+)"),
    ],
}


def find_names(source, language):
    if language == "python":
        return python_names(source)
    text = blank_out_text(source)
    matches = (m for pattern in NAME_PATTERNS[language] for m in pattern.finditer(text))
    return [m.group("name") for m in matches if m.group("name") != "_"]


def names_in_project(project):
    return [
        name
        for path in project.files(*SUFFIX_LANGUAGE)
        for name in find_names(path.read_text(errors="ignore"), SUFFIX_LANGUAGE[path.suffix])
    ]
