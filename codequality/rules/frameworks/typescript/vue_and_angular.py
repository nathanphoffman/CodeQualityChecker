import re

from ....models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import TYPESCRIPT, TYPESCRIPT_SUFFIXES, non_test_files, read_source
from ...check_helpers import fail_on_hits, pattern_hits

VUE_FILES = (".vue",)

# Vue rules need no language: a vue project may be plain JavaScript, and the vue dependency is enough to know they apply.
# v-html= on an element, which puts raw text into the page as HTML
HTML_BINDING = re.compile(r"\bv-html=")

# An opening tag that has v-for but no :key (or v-bind:key) anywhere in it. The (?!...) parts stop the match from stepping over a key,
# so a tag that has one, before or after its v-for, is not found.
LOOP_WITHOUT_KEY = re.compile(r"<[\w-]+\s(?:(?!:key|v-bind:key)[^>])*\bv-for=(?:(?!:key|v-bind:key)[^>])*>")

# bypassSecurityTrustHtml / Script / Style / Url / ResourceUrl, the calls that tell Angular to stop cleaning a value
SANITIZER_BYPASS = re.compile(r"\bbypassSecurityTrust\w+\(")

# @Component( starts a component; ChangeDetectionStrategy.OnPush is how one opts in to cheaper change checking
COMPONENT = re.compile(r"@Component\(")
ON_PUSH = re.compile(r"ChangeDetectionStrategy\.OnPush")

@rule("TS-VUE-001", "vue: no v-html", framework="vue", severity=SEVERITY_ERROR)
def vue_html_binding(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, VUE_FILES, HTML_BINDING), "v-html shows raw HTML, so any script in the text runs")

@rule("TS-VUE-002", "vue: every v-for has a :key", framework="vue", severity=SEVERITY_INFO)
def vue_loop_keys(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, VUE_FILES, LOOP_WITHOUT_KEY), "v-for without :key, so items get mixed up when the list changes")

@rule("TS-ANGULAR-001", "angular: the sanitizer is not bypassed", language=TYPESCRIPT, framework="angular", severity=SEVERITY_ERROR)
def angular_sanitizer(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, TYPESCRIPT_SUFFIXES, SANITIZER_BYPASS), "bypassSecurityTrust turns off Angular's protection against injected scripts")

@rule("TS-ANGULAR-002", "angular: components use OnPush change detection", language=TYPESCRIPT, framework="angular", severity=SEVERITY_INFO)
def angular_on_push(project: Project) -> Result:
    texts = [read_source(path) for path in non_test_files(project, TYPESCRIPT_SUFFIXES)]
    components, on_push = (sum(len(pattern.findall(text)) for text in texts) for pattern in (COMPONENT, ON_PUSH))

    if not components:
        return Result.passed("no components found")

    return Result.scored(on_push / components, f"{components - on_push} of {components} components check for changes on every event")
