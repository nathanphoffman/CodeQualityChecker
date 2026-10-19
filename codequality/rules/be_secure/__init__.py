"""Rule 5: Be secure. Looks for secrets in code, and for risky calls and constructs."""
from functools import partial

from ...registry import rule
from .call_checks import CALL_CHECKS
from .judge_uses import grade_findings, run_call_check
from .secrets import hardcoded_secrets, judge_secret_files
from ...models import SEVERITY_ERROR

for check in CALL_CHECKS:
    rule(check.id, check.title, severity=check.severity)(partial(run_call_check, check))

@rule("RULE-05-HARDCODED-SECRETS", "No passwords, keys or tokens written in the code", severity=SEVERITY_ERROR)
def check_hardcoded_secrets(project):
    return grade_findings(*hardcoded_secrets(project))

@rule("RULE-05-SECRET-FILES", "Key and .env files are listed in .gitignore", severity=SEVERITY_ERROR)
def check_secret_files(project):
    return judge_secret_files(project)
