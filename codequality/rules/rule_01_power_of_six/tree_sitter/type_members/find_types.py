from .....source_code import DEOR, PYTHON
from ...deor.deor_types import deor_types
from ...python.python_types import python_types
from .tree_types import tree_types

def find_types(source, language):
    """A Type_Info for every type the source declares, with its field and method counts."""
    if language == PYTHON:
        return python_types(source)

    if language == DEOR:
        return deor_types(source)

    return sorted(tree_types(source, language), key=lambda info: info.line_number)
