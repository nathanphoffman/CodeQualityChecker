import re

from ...models import SEVERITY_ERROR, Project, Result
from ...registry import rule
from ...source_code import RUST
from ..check_helpers import fail_on_hits, named_file_hits, pattern_hits

# DefaultBodyLimit::disable(), which lets a client upload a body of any size
BODY_LIMIT_OFF = re.compile(r"DefaultBodyLimit::disable\(\)")

# Calls that hold up the whole thread: std::thread::sleep and anything from std::fs (tokio::fs is the async version)
BLOCKING_CALL = re.compile(r"std::thread::sleep\(|std::fs::\w+\(")

# `"csp": null` in tauri.conf.json: no Content Security Policy, so injected scripts run freely
CSP_OFF = re.compile(r'"csp"\s*:\s*null')

# `"all": true` (every API of a Tauri v1 allowlist on) or the dangerous remote-access switch
ALLOW_EVERYTHING = re.compile(r'"all"\s*:\s*true|"dangerousRemoteDomainIpcAccess"')

TAURI_CONFIG = ("tauri.conf.json",)

def blocking_in_async(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".rs",), BLOCKING_CALL), "blocking std::thread::sleep or std::fs calls in an async server (use tokio's)")

# Axum and Actix run on async runtimes, so one blocking call stalls every request on that thread.
rule("RUST-AXUM-002", "axum: no blocking calls in the async server", language=RUST, framework="axum")(blocking_in_async)
rule("RUST-ACTIX-001", "actix: no blocking calls in the async server", language=RUST, framework="actix")(blocking_in_async)

@rule("RUST-AXUM-001", "axum: request body size limit is not switched off", language=RUST, framework="axum", severity=SEVERITY_ERROR)
def axum_body_limit(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".rs",), BODY_LIMIT_OFF), "DefaultBodyLimit::disable() accepts bodies of any size")

@rule("RUST-TAURI-001", "tauri: a Content Security Policy is set", language=RUST, framework="tauri", severity=SEVERITY_ERROR)
def tauri_csp(project: Project) -> Result:
    return fail_on_hits(named_file_hits(project, TAURI_CONFIG, CSP_OFF), "csp is null in the Tauri config")

@rule("RUST-TAURI-002", "tauri: the allowlist doesn't switch everything on", language=RUST, framework="tauri", severity=SEVERITY_ERROR)
def tauri_allowlist(project: Project) -> Result:
    return fail_on_hits(named_file_hits(project, TAURI_CONFIG, ALLOW_EVERYTHING), "every API is allowed in the Tauri config")
