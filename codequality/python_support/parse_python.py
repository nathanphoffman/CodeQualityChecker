import ast
import warnings


def parse_python(source):
    try:
        return ast.parse(source)
    except SyntaxError as error:
        warnings.warn(f"skipped Python source that does not parse: {error}")
        return ast.Module(body=[], type_ignores=[])
