import re

from ....models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import PYTHON, non_test_files, read_source
from ...check_helpers import fail_on_hits, pattern_hits
from . import data_libraries  # noqa: F401  (importing registers the rules)
from .blocking_calls import blocking_calls

PYTHON_FILES = (".py",)

# ALLOWED_HOSTS, then =, then a list holding the string "*" (either quote), possibly after other hosts
WILDCARD_HOSTS = re.compile(r"ALLOWED_HOSTS\s*=\s*\[[^\]]*['\"]\*['\"]")

# DEBUG = True at the start of a line (settings files), not DEBUG = os.environ.get(...)
DEBUG_ON = re.compile(r"^DEBUG\s*=\s*True\b", re.M)

# the @csrf_exempt decorator, which switches off Django's cross-site request forgery check for a view
CSRF_EXEMPT = re.compile(r"@csrf_exempt\b")

# render_template_string( whose first argument does not start with a plain quote, so it is a variable or an f-string being rendered as a template
TEMPLATE_FROM_VARIABLE = re.compile(r"render_template_string\(\s*(?![\"'])")

# A route decorator (@app.get, @router.post...) with its arguments, the def below it, and an optional `->` after the parameters.
# The lazy `.*?` parts stretch just far enough to get past brackets inside the arguments, like Depends(get_db).
ROUTE = re.compile(r"@\w+\.(?:get|post|put|patch|delete)\((?P<decorator>.*?)\)\s*\n\s*(?:async\s+)?def\s+\w+\(.*?\)(?P<arrow>\s*->)?\s*:", re.S)

@rule("PYTHON-DJANGO-001", "django: ALLOWED_HOSTS is not a wildcard", language=PYTHON, framework="django", severity=SEVERITY_ERROR)
def django_allowed_hosts(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, WILDCARD_HOSTS), 'ALLOWED_HOSTS accepts any host ("*")')

@rule("PYTHON-DJANGO-002", "django: DEBUG is not hard-coded to True", language=PYTHON, framework="django", severity=SEVERITY_ERROR)
def django_debug(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, DEBUG_ON), "DEBUG is always on, so errors show code and settings to visitors")

@rule("PYTHON-DJANGO-003", "django: no views exempt from CSRF protection", language=PYTHON, framework="django")
def django_csrf(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, CSRF_EXEMPT), "@csrf_exempt turns the protection off")

@rule("PYTHON-FLASK-001", "flask: templates are not built from variables", language=PYTHON, framework="flask", severity=SEVERITY_ERROR)
def flask_template_strings(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, TEMPLATE_FROM_VARIABLE), "render_template_string with a non-literal template (injection risk)")

@rule("PYTHON-FASTAPI-001", "fastapi: every route says what it returns", language=PYTHON, framework="fastapi", severity=SEVERITY_INFO)
def fastapi_return_types(project: Project) -> Result:
    # two loops: every route match in every non-test Python file
    routes = [match for path in non_test_files(project, PYTHON_FILES) for match in ROUTE.finditer(read_source(path))]

    if not routes:
        return Result.passed("no routes found")

    declared = [route for route in routes if route.group("arrow") or "response_model" in route.group("decorator")]

    return Result.scored(len(declared) / len(routes), f"{len(routes) - len(declared)} of {len(routes)} routes have no response_model or -> type")

@rule("PYTHON-FASTAPI-002", "fastapi: async routes don't block the event loop", language=PYTHON, framework="fastapi")
def fastapi_blocking(project: Project) -> Result:
    return fail_on_hits(blocking_calls(project), "time.sleep or requests calls inside `async def` freeze every request")
