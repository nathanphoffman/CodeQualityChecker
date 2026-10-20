from ....source_code import DEOR, PYTHON, SUFFIX_LANGUAGE, read_source
from ..deor.deor_calls import deor_calls
from ..python.python_calls import python_calls
from ..tree_sitter.text_calls import text_calls
from .longest_chain import longest_chains

def calls_in_source(source, language):
    if language == PYTHON:
        return python_calls(source)

    return deor_calls(source) if language == DEOR else text_calls(source, language)

def build_graph(project):
    """({function name: names it calls that this project defines}, {function name: "file:line" of its first definition})."""
    calls, where = {}, {}

    for path in project.files(*SUFFIX_LANGUAGE):
        for name, line_number, called in calls_in_source(read_source(path), SUFFIX_LANGUAGE[path.suffix]):
            calls.setdefault(name, set()).update(called)
            where.setdefault(name, f"{project.label_for(path)}:{line_number}")

    return {name: called & calls.keys() - {name} for name, called in calls.items()}, where

def call_depths(project):
    """Maps each entry point (a function nothing else calls) to its deepest chain of calls, written out, with the depth as the value."""
    graph, where = build_graph(project)
    chains = longest_chains(graph)

    return {f"{where[chain[0]]} {' -> '.join(chain)}": len(chain) for chain in chains}
