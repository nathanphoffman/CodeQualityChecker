import re

from ....models import SEVERITY_ERROR, SEVERITY_INFO, Project, Result
from ....registry import rule
from ....source_code import PYTHON
from ...check_helpers import fail_on_hits, pattern_hits

PYTHON_FILES = (".py",)

# text( whose SQL is an f-string, or a "string" joined on with +, % or .format( : SQL built from variables
SQL_TEXT_FROM_PARTS = re.compile(r"\btext\(\s*(?:[fF][\"']|[\"'][^\"'\n]*[\"']\s*(?:\+|%|\.format\())")

# session.query( or db.query(, the SQLAlchemy 1.x way of asking for rows (2.0 uses select())
LEGACY_QUERY = re.compile(r"\b(?:session|db)\.query\(")

# Pydantic v1 methods (parse_obj, parse_raw, from_orm, update_forward_refs) and the v1-style `class Config:` block
PYDANTIC_V1 = re.compile(r"\.(?:parse_obj|parse_raw|from_orm|update_forward_refs)\(|^\s+class Config\s*:", re.M)

# extra="allow" or extra=Extra.allow, which keeps unknown fields instead of rejecting them
EXTRA_ALLOWED = re.compile(r"\bextra\s*=\s*(?:[\"']allow[\"']|Extra\.allow)")

@rule("PYTHON-SQLALCHEMY-001", "sqlalchemy: text() SQL is not built from strings", language=PYTHON, framework="sqlalchemy", severity=SEVERITY_ERROR)
def sqlalchemy_text_sql(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, SQL_TEXT_FROM_PARTS), "text() with joined or interpolated SQL (use :name parameters)")

@rule("PYTHON-SQLALCHEMY-002", "sqlalchemy: no legacy session.query()", language=PYTHON, framework="sqlalchemy", severity=SEVERITY_INFO)
def sqlalchemy_legacy_query(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, LEGACY_QUERY), "session.query() is the old style")

@rule("PYTHON-PYDANTIC-001", "pydantic: no v1-style methods or Config class", language=PYTHON, framework="pydantic", severity=SEVERITY_INFO)
def pydantic_v1_style(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, PYDANTIC_V1), "Pydantic v1 methods or `class Config:`")

@rule("PYTHON-PYDANTIC-002", "pydantic: models reject unknown fields", language=PYTHON, framework="pydantic")
def pydantic_extra_fields(project: Project) -> Result:
    return fail_on_hits(pattern_hits(project, PYTHON_FILES, EXTRA_ALLOWED), "extra=allow keeps fields nobody declared")
