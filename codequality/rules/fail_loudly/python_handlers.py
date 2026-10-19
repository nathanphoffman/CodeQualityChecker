import ast

from ...python_support.parse_python import parse_python
from ..be_secure.uses.python_uses import dotted_name
from .Error_Handler import Error_Handler
from .limits import BROAD_EXCEPTIONS, LOUD_NAME_ENDINGS, LOUD_RECEIVERS


def is_loud_name(name):
    """Whether a call like logging.error, print, console.log or sys.exit speaks up about a problem."""
    parts = name.split(".")
    return parts[-1] in LOUD_NAME_ENDINGS or parts[0] in LOUD_RECEIVERS


def is_broad(handler):
    return handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id in BROAD_EXCEPTIONS)


def returns_answer(handler):
    """A handler for one expected kind of error that ends by returning a real value is giving an answer, not hiding."""
    last = handler.body[-1]
    return isinstance(last, ast.Return) and last.value is not None and not (isinstance(last.value, ast.Constant) and last.value.value is None)


def is_loud(handler):
    if not is_broad(handler) and returns_answer(handler):
        return True
    nodes = [node for statement in handler.body for node in ast.walk(statement)]
    raises = any(isinstance(node, ast.Raise) for node in nodes)
    uses_error = handler.name is not None and any(isinstance(node, ast.Name) and node.id == handler.name for node in nodes)
    return raises or uses_error or any(isinstance(node, ast.Call) and is_loud_name(dotted_name(node.func)) for node in nodes)


def python_handlers(source):
    found = []
    for node in ast.walk(parse_python(source)):
        if isinstance(node, ast.ExceptHandler):
            found.append(Error_Handler(node.lineno, True, is_loud(node), is_broad(node)))
        elif isinstance(node, ast.Raise):
            found.append(Error_Handler(node.lineno, False, True, False))
    return found
