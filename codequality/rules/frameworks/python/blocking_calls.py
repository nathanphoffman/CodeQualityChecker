import ast

from ....language_parsers.python.parse_python import parse_python
from ....models import Project
from ....source_code import non_test_files, read_source

# Calls that wait without letting other requests run when made inside `async def`.
BLOCKING_CALLS = {"time.sleep", "requests.get", "requests.post", "requests.put", "requests.patch", "requests.delete", "requests.request",
                  "urllib.request.urlopen"}

def blocking_calls(project: Project) -> list[str]:
    """'file:line' for each blocking call made inside an `async def`."""
    hits = set()

    for path in non_test_files(project, (".py",)):
        for function in ast.walk(parse_python(read_source(path))):
            if isinstance(function, ast.AsyncFunctionDef):
                hits.update(f"{project.label_for(path)}:{call.lineno}" for call in ast.walk(function)
                            if isinstance(call, ast.Call) and ast.unparse(call.func) in BLOCKING_CALLS)

    return sorted(hits)
