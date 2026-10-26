import re

from ....models import SEVERITY_ERROR, Project, Result
from ....registry import rule
from ....source_code import GO
from ...check_helpers import fail_on_hits, pattern_hits

GO_FILES = (".go",)

# http.ListenAndServe( or http.ListenAndServeTLS(, which start a server with no read or write timeouts
BARE_SERVER = re.compile(r"\bhttp\.ListenAndServe(?:TLS)?\(")

# http.Get / Post / Head / PostForm and http.DefaultClient, which have no timeout, so one slow server hangs the caller forever
BARE_CLIENT = re.compile(r"\bhttp\.(?:Get|Post|Head|PostForm)\(|\bhttp\.DefaultClient\b")

# .Raw( .Exec( .Where( or .Order( given fmt.Sprintf(...) or a "string" joined on with +: SQL built from variables
GORM_SQL_FROM_PARTS = re.compile(r"\.(?:Raw|Exec|Where|Order)\(\s*(?:fmt\.Sprintf\(|\"[^\"\n]*\"\s*\+)")

@rule("GO-NETHTTP-001", "net/http: servers have timeouts", language=GO, framework="nethttp")
def nethttp_server_timeouts(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, GO_FILES, BARE_SERVER), "http.ListenAndServe has no timeouts (use an http.Server with ReadHeaderTimeout)")

@rule("GO-NETHTTP-002", "net/http: clients have timeouts", language=GO, framework="nethttp")
def nethttp_client_timeouts(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, GO_FILES, BARE_CLIENT), "http.Get and http.DefaultClient never give up (use an http.Client with Timeout)")

@rule("GO-GORM-001", "gorm: SQL is not built from strings", language=GO, framework="gorm", severity=SEVERITY_ERROR)
def gorm_sql_from_parts(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, GO_FILES, GORM_SQL_FROM_PARTS), "Raw/Exec/Where with Sprintf or + (use ? placeholders)")
