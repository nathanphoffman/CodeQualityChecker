from ...python_support.python_bodies import python_bodies
from ...source_code import SUFFIX_LANGUAGE
from ...tree_sitter_support.tree_functions import tree_bodies
from .Function_Body import Function_Body


def find_bodies(source, language):
    found = python_bodies(source) if language == "python" else tree_bodies(source, language)
    return [Function_Body(*fields) for fields in found]


def bodies_in_project(project):
    """Maps "file:line name" to the Function_Body found there."""
    bodies = {}
    for path in project.files(*SUFFIX_LANGUAGE):
        label = project.label_for(path)
        for body in find_bodies(path.read_text(errors="ignore"), SUFFIX_LANGUAGE[path.suffix]):
            bodies[f"{label}:{body.line_number} {body.name}"] = body
    return bodies
