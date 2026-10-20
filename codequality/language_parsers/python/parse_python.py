import ast
import warnings
from functools import lru_cache

MAX_CACHED_FILES = 2048  # every rule parses every file, so keeping the trees means each file is parsed once per run

@lru_cache(maxsize=MAX_CACHED_FILES)
def parse_python(source):
    try:
        return ast.parse(source)
    except SyntaxError as error:
        warnings.warn(f"skipped Python source that does not parse: {error}")

        return ast.Module(body=[], type_ignores=[])
