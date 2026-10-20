from ..deor.deor_bodies import deor_bodies
from ..python.python_bodies import python_bodies
from ....source_code import DEOR, PYTHON, SUFFIX_LANGUAGE, read_source
from ....language_parsers.tree_sitter.tree_functions import tree_bodies
from .Function_Body import Function_Body

def find_bodies(source, language):
    found = python_bodies(source) if language == PYTHON else deor_bodies(source) if language == DEOR else tree_bodies(source, language)

    return [Function_Body(*fields) for fields in found]

def bodies_in_project(project):
    """Maps "file:line name" to the Function_Body found there."""
    bodies = {}

    for path in project.files(*SUFFIX_LANGUAGE):
        label = project.label_for(path)

        for body in find_bodies(read_source(path), SUFFIX_LANGUAGE[path.suffix]):
            bodies[f"{label}:{body.line_number} {body.name}"] = body

    return bodies
