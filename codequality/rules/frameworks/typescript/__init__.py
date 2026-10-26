import re

from ....models import SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import TYPESCRIPT, TYPESCRIPT_SUFFIXES
from ...check_helpers import fail_on_hits, fail_unless_found, pattern_hits
from . import svelte_nuxt_fastify, vue_and_angular  # noqa: F401  (importing registers the rules)

# key={i}, key={idx}, key={index} or key={anythingIndex}: list items keyed by their position get mixed up when the list changes
INDEX_KEY = re.compile(r"key=\{\s*(?:i|idx|\w*[iI]ndex)\s*\}")

# document.getElementById / querySelector / querySelectorAll, which reach around React instead of using refs
DOM_LOOKUP = re.compile(r"document\.(?:getElementById|querySelector|querySelectorAll)\(")

# helmet( being called, which is how Express apps set their security headers
HELMET_USED = re.compile(r"\bhelmet\(")

# an error handler's first two parameters: a name starting with err, then req (Express spots error handlers by their four parameters)
ERROR_HANDLER = re.compile(r"\berr\w*\s*(?::\s*[\w.]+)?,\s*req\b")

# ValidationPipe, Nest's built-in checker for incoming request bodies
VALIDATION_PIPE = re.compile(r"\bValidationPipe\b")

# @Body() body: any, a request body that skips the DTO check
ANY_BODY = re.compile(r"@Body\(\)\s*\w+\s*:\s*any\b")

@rule("TS-REACT-001", "react: list items are not keyed by their index", language=TYPESCRIPT, framework="react", severity=SEVERITY_INFO)
def react_index_keys(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, TYPESCRIPT_SUFFIXES, INDEX_KEY), "key is the array index")

@rule("TS-REACT-002", "react: no direct DOM lookups", language=TYPESCRIPT, framework="react", severity=SEVERITY_INFO)
def react_dom_lookups(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, TYPESCRIPT_SUFFIXES, DOM_LOOKUP), "document lookups instead of refs")

@rule("TS-EXPRESS-001", "express: helmet sets security headers", language=TYPESCRIPT, framework="express")
def express_helmet(project: Project) -> Result:
    return fail_unless_found(project, TYPESCRIPT_SUFFIXES, HELMET_USED, "helmet() is never called")

@rule("TS-EXPRESS-002", "express: has an error-handling middleware", language=TYPESCRIPT, framework="express")
def express_error_handler(project: Project) -> Result:
    return fail_unless_found(project, TYPESCRIPT_SUFFIXES, ERROR_HANDLER, "no (err, req, res, next) handler found")

@rule("TS-NEST-001", "nest: ValidationPipe checks incoming data", language=TYPESCRIPT, framework="nest")
def nest_validation(project: Project) -> Result:
    return fail_unless_found(project, TYPESCRIPT_SUFFIXES, VALIDATION_PIPE, "ValidationPipe is never used")

@rule("TS-NEST-002", "nest: request bodies are typed, not any", language=TYPESCRIPT, framework="nest")
def nest_any_body(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, TYPESCRIPT_SUFFIXES, ANY_BODY), "@Body() typed as any")
