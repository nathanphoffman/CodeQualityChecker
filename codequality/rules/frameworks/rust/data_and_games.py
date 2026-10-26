import re

from ....models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import RUST
from ...check_helpers import fail_on_hits, pattern_hits

# sql_query( given format!(...), which is Diesel's raw SQL built from variables
DIESEL_FORMATTED_SQL = re.compile(r"\bsql_query\(\s*&?format!\(")

# query( / query_as( / query_scalar( (with an optional ::<types>) given format!(...), which is SQLx's SQL built from variables
SQLX_FORMATTED_SQL = re.compile(r"\bquery(?:_as|_scalar)?(?:::<[^>]*>)?\(\s*&?format!\(")

# std::thread::sleep(, which stops the thread that runs the whole game loop
THREAD_SLEEP = re.compile(r"std::thread::sleep\(")

@rule("RUST-DIESEL-001", "diesel: sql_query is not built with format!", language=RUST, framework="diesel", severity=SEVERITY_ERROR)
def diesel_formatted_sql(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".rs",), DIESEL_FORMATTED_SQL), "sql_query(format!(...)) lets input change the query (use .bind)")

@rule("RUST-SQLX-001", "sqlx: queries are not built with format!", language=RUST, framework="sqlx", severity=SEVERITY_ERROR)
def sqlx_formatted_sql(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".rs",), SQLX_FORMATTED_SQL), "query(format!(...)) lets input change the query (use .bind)")

@rule("RUST-BEVY-001", "bevy: no thread sleeping", language=RUST, framework="bevy", severity=SEVERITY_INFO)
def bevy_thread_sleep(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, (".rs",), THREAD_SLEEP), "std::thread::sleep freezes the whole game")
