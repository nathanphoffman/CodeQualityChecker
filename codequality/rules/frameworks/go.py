import re

from ...models import SEVERITY_INFO, Project, Result
from ...registry import rule
from ...source_code import GO
from ..check_helpers import fail_on_hits, fail_unless_found, pattern_hits

GO_FILES = (".go",)

# gin.SetMode( being called, or GIN_MODE being read: either way release mode can be chosen
GIN_MODE_SET = re.compile(r"gin\.SetMode\(|GIN_MODE")

# SetTrustedProxies( or the TrustedProxies setting, which says which proxies may set the client's IP
GIN_PROXIES_SET = re.compile(r"SetTrustedProxies\(|TrustedProxies")

# middleware.Recover(, which turns a panic in a handler into an error response (Echo does not do this by default)
ECHO_RECOVER = re.compile(r"middleware\.Recover\(")

# .Debug = true, Echo's debug mode that shows internal error details
ECHO_DEBUG = re.compile(r"\.Debug\s*=\s*true")

# recover.New(, Fiber's panic-catching middleware
FIBER_RECOVER = re.compile(r"recover\.New\(")

@rule("GO-GIN-001", "gin: release mode is chosen", language=GO, framework="gin", severity=SEVERITY_INFO)
def gin_release_mode(project: Project) -> Result:
    return fail_unless_found(project, GO_FILES, GIN_MODE_SET, "gin.SetMode or GIN_MODE is never used, so it runs in debug mode")

@rule("GO-GIN-002", "gin: trusted proxies are set", language=GO, framework="gin", severity=SEVERITY_INFO)
def gin_trusted_proxies(project: Project) -> Result:
    return fail_unless_found(project, GO_FILES, GIN_PROXIES_SET, "SetTrustedProxies is never called, so any client can fake its IP")

@rule("GO-ECHO-001", "echo: panics are recovered", language=GO, framework="echo")
def echo_recover(project: Project) -> Result:
    return fail_unless_found(project, GO_FILES, ECHO_RECOVER, "middleware.Recover() is never used, so a panic ends the request with no answer")

@rule("GO-ECHO-002", "echo: debug mode is not switched on", language=GO, framework="echo")
def echo_debug(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, GO_FILES, ECHO_DEBUG), "Debug = true shows internal errors to clients")

@rule("GO-FIBER-001", "fiber: panics are recovered", language=GO, framework="fiber")
def fiber_recover(project: Project) -> Result:
    return fail_unless_found(project, GO_FILES, FIBER_RECOVER, "recover.New() is never used, so a panic takes the server down")
