import ast

from ....language_parsers.python.parse_python import parse_python
from ..shared.Type_Info import Type_Info

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
CONSTRUCTOR = "__init__"  # a constructor is not counted as one of the type's methods

def field_count(statement):
    """The names a class-body assignment creates: `a = 1`, `a: int = 1` or `a = b = 1`."""

    if isinstance(statement, ast.Assign):
        return sum(isinstance(target, ast.Name) for target in statement.targets)

    return int(isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name))

def python_types(source):
    """A Type_Info for every class. Only class-level fields count, since fields set in __init__ are not declared."""
    classes = [node for node in ast.walk(parse_python(source)) if isinstance(node, ast.ClassDef)]

    return [Type_Info(node.name, node.lineno, sum(field_count(statement) for statement in node.body),
                      sum(isinstance(statement, FUNCTIONS) and statement.name != CONSTRUCTOR for statement in node.body))
            for node in classes]
