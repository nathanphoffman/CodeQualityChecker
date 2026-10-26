import re

from ...models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ...registry import rule
from ...source_code import CSHARP
from ..check_helpers import fail_on_hits, fail_unless_found, pattern_hits

CSHARP_FILES = (".cs", ".razor")

# UseHttpsRedirection(), which sends plain HTTP visitors to HTTPS
HTTPS_REDIRECT = re.compile(r"UseHttpsRedirection\(\)")

# UseHsts(), which tells browsers to only ever use HTTPS for this site
HSTS = re.compile(r"UseHsts\(\)")

# FromSqlRaw / ExecuteSqlRaw / SqlQueryRaw whose SQL starts with $" (an interpolated string) or a "text" + joined on, which lets input change the query
RAW_SQL_FROM_PARTS = re.compile(r"\b(?:FromSql|ExecuteSql|SqlQuery)Raw\w*\(\s*(?:@?\$@?\"|\"[^\"\n]*\"\s*\+)")

# .Result, .Wait() and .GetAwaiter().GetResult(), the ways of waiting for async work by freezing the thread
BLOCKING_WAIT = re.compile(r"\.Result\b|\.Wait\(\)|\.GetAwaiter\(\)\.GetResult\(\)")

def blocking_wait(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, CSHARP_FILES, BLOCKING_WAIT), "waiting on a Task with .Result or .Wait() freezes the thread (use await)")

# Web code and Blazor components both run many requests or UI events on few threads, so blocking one hurts them all.
rule("CSHARP-ASPNET-003", "aspnet: no blocking waits on async work", language=CSHARP, framework="aspnet", severity=SEVERITY_INFO)(blocking_wait)
rule("CSHARP-BLAZOR-001", "blazor: no blocking waits on async work", language=CSHARP, framework="blazor", severity=SEVERITY_INFO)(blocking_wait)

@rule("CSHARP-ASPNET-001", "aspnet: HTTP is redirected to HTTPS", language=CSHARP, framework="aspnet")
def aspnet_https(project: Project) -> Result:
    return fail_unless_found(project, CSHARP_FILES, HTTPS_REDIRECT, "app.UseHttpsRedirection() is never called")

@rule("CSHARP-ASPNET-002", "aspnet: HSTS is on", language=CSHARP, framework="aspnet", severity=SEVERITY_INFO)
def aspnet_hsts(project: Project) -> Result:
    return fail_unless_found(project, CSHARP_FILES, HSTS, "app.UseHsts() is never called")

@rule("CSHARP-EFCORE-001", "efcore: raw SQL is not built from strings", language=CSHARP, framework="efcore", severity=SEVERITY_ERROR)
def efcore_raw_sql(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, CSHARP_FILES, RAW_SQL_FROM_PARTS), "raw SQL joined or interpolated from variables (use FromSql or parameters)")
