import ast

from ....language_parsers.python.parse_python import parse_python

RECEIVER_NAMES = {"self", "cls"}

def count_arguments(arguments):
    named = arguments.posonlyargs + arguments.args + arguments.kwonlyargs
    extras = [arguments.vararg, arguments.kwarg]

    return len([argument for argument in named if argument.arg not in RECEIVER_NAMES]) + len([extra for extra in extras if extra])

def python_functions(source):
    """(name, argument_count, line_count, line_number) for every def."""
    definitions = (ast.FunctionDef, ast.AsyncFunctionDef)

    return [
        (node.name, count_arguments(node.args), node.end_lineno - node.lineno + 1, node.lineno)
        for node in ast.walk(parse_python(source))
        if isinstance(node, definitions)
    ]
