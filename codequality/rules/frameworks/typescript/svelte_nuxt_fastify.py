import re

from ....models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import TYPESCRIPT, TYPESCRIPT_SUFFIXES, non_test_files, read_source
from ...check_helpers import fail_on_hits, fail_unless_found, named_file_hits, pattern_hits

SVELTE_FILES = (".svelte",)
NUXT_CONFIG = ("nuxt.config.ts", "nuxt.config.js", "nuxt.config.mjs")

# Svelte, Nuxt and Fastify projects can be plain JavaScript, so the Svelte and Nuxt rules need no language: the dependency is enough.

# {@html ...}, Svelte's way of putting raw text into the page as HTML
HTML_TAG = re.compile(r"\{@html\b")

# {#each ...} with no ( ) after the list, so no (key) says which item is which
EACH_WITHOUT_KEY = re.compile(r"\{#each\s+[^}(]*\}")

# `public: {` in nuxt.config, then (before its closing brace) a name that sounds private: such runtimeConfig values are sent to every browser
PUBLIC_CONFIG_SECRET = re.compile(r"public\s*:\s*\{[^}]*?(?:secret|token|password|private|api_?key)", re.I)

# readBody( or getQuery(, which hand back whatever the client sent; readValidatedBody and getValidatedQuery check it first
UNVALIDATED_INPUT = re.compile(r"\b(?:readBody|getQuery)\(")

# A route registration with a /path, and one whose options object (after the path) mentions schema
ROUTE = re.compile(r"\.(?:get|post|put|patch|delete)\(\s*[\"'`]/[^\"'`]*[\"'`]\s*,")
ROUTE_WITH_SCHEMA = re.compile(r"\.(?:get|post|put|patch|delete)\(\s*[\"'`]/[^\"'`]*[\"'`]\s*,\s*\{[^}]*\bschema\b")

# logger: in the options passed to fastify(...)
LOGGER_OPTION = re.compile(r"\blogger\s*:")

@rule("TS-SVELTE-001", "svelte: no {@html}", framework="svelte", severity=SEVERITY_ERROR)
def svelte_html_tag(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, SVELTE_FILES, HTML_TAG), "{@html} shows raw HTML, so any script in the text runs")

@rule("TS-SVELTE-002", "svelte: every {#each} has a key", framework="svelte", severity=SEVERITY_INFO)
def svelte_each_keys(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, SVELTE_FILES, EACH_WITHOUT_KEY), "{#each} without a (key), so items get mixed up when the list changes")

@rule("TS-NUXT-001", "nuxt: no secrets in public runtimeConfig", framework="nuxt", severity=SEVERITY_ERROR)
def nuxt_public_secrets(project: Project) -> Result:
    return fail_on_hits(named_file_hits(project, NUXT_CONFIG, PUBLIC_CONFIG_SECRET), "browser-visible config with a secret-sounding name")

@rule("TS-NUXT-002", "nuxt: request data is validated", framework="nuxt", severity=SEVERITY_INFO)
def nuxt_validated_input(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".ts", ".js"), UNVALIDATED_INPUT), "readBody or getQuery used without validation")

@rule("TS-FASTIFY-001", "fastify: routes declare a schema", language=TYPESCRIPT, framework="fastify")
def fastify_schemas(project: Project) -> Result:
    texts = [read_source(path) for path in non_test_files(project, TYPESCRIPT_SUFFIXES)]
    routes, with_schema = (sum(len(pattern.findall(text)) for text in texts) for pattern in (ROUTE, ROUTE_WITH_SCHEMA))

    if not routes:
        return Result.passed("no routes found")

    return Result.scored(with_schema / routes, f"{routes - with_schema} of {routes} routes have no schema")

@rule("TS-FASTIFY-002", "fastify: logging is configured", language=TYPESCRIPT, framework="fastify", severity=SEVERITY_INFO)
def fastify_logger(project: Project) -> Result:
    return fail_unless_found(project, TYPESCRIPT_SUFFIXES, LOGGER_OPTION, "no `logger:` option, and Fastify logs nothing by default")
