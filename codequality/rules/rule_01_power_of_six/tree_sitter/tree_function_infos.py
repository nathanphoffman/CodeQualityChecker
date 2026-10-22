from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.syntax_shapes import FUNCTION_TYPES
from ....language_parsers.tree_sitter.tree_functions import function_name
from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.Function_Info import Function_Info

# Mojo and Fortran have no braces to count, and C# declarations have no keyword to find (`public int Name(`), so their functions
# are measured from the syntax tree instead of by pattern.
# Mojo's `self` is not an argument, the same as Python's.
RECEIVER_NAMES = {"self"}
ARGUMENT_TYPES = {"parameter", "identifier"}

def parameters_of(function):
    """The `parameters` node: Mojo has it on the function, Fortran has it on the function's header line."""

    for node in [function] + function.children:
        if node.child_by_field_name("parameters") is not None:
            return node.child_by_field_name("parameters")

    return None

def argument_count(function):
    """Mojo lists `parameter` nodes under `parameters`; Fortran lists the bare argument names there."""
    parameters = parameters_of(function)
    arguments = [] if parameters is None else [node for node in parameters.named_children if node.type in ARGUMENT_TYPES]
    names = [argument.child_by_field_name("name") or argument for argument in arguments]

    return len([name for name in names if name.text.decode() not in RECEIVER_NAMES])

def tree_function_infos(source, language):
    """A Function_Info for every function, from its first line to its last."""
    functions = [node for node in walk(parse_tree(source, language)) if node.type in FUNCTION_TYPES[language]]

    return [Function_Info(function_name(function), argument_count(function), function.end_point.row - function.start_point.row + 1,
                          function.start_point.row + 1) for function in functions]
