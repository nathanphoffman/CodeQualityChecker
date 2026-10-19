"""Rule 12: Clean up. Finds unused imports, leftover variables, unreachable code, unused private functions and commented-out code."""
from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from ...source_code import items_in_project
from ..comment_why.extract import python_comments, tree_comments
from ..comment_why.judging.signals import is_commented_out_code

from .project_cleanup import analyze_project, unused_private_definitions

def grade_leftovers(total, places, noun):
    """Score is the share of items that are clean. `places` are "file:line" strings, one per leftover."""

    if not total:
        return Result.passed(f"no {noun} found")

    listed = ", ".join(places[:MAX_LISTED_OFFENDERS])
    message = f"{len(places)} of {total} {noun}: {listed}" if places else ""

    return Result.scored(1 - len(places) / total, message)

def places_in(analyzed, field):
    return [f"{label}:{line}" for label, findings, _ in analyzed for line in getattr(findings, field)]

@rule("RULE-12-UNUSED-IMPORTS", "Every import is used")
def check_unused_imports(project):
    analyzed = [(label, findings, usage) for label, findings, usage in analyze_project(project)]
    total = sum(findings.imports_total for _, findings, _ in analyzed)

    return grade_leftovers(total, places_in(analyzed, "unused_imports"), "imported names are unused")

@rule("RULE-12-LEFTOVER-VARIABLES", "Every variable is read")
def check_leftover_variables(project):
    analyzed = analyze_project(project)
    total = sum(findings.variables_total for _, findings, _ in analyzed)

    return grade_leftovers(total, places_in(analyzed, "unused_variables"), "local variables are never read")

@rule("RULE-12-UNREACHABLE-CODE", "No code after a return, raise, break or continue")
def check_unreachable_code(project):
    analyzed = analyze_project(project)
    total = sum(findings.statements_total for _, findings, _ in analyzed)

    return grade_leftovers(total, places_in(analyzed, "unreachable"), "statements can never run")

@rule("RULE-12-UNUSED-PRIVATE-FUNCTIONS", "Every private function is used")
def check_unused_private_functions(project):
    analyzed = analyze_project(project)
    total = sum(len(usage.private_definitions) for _, _, usage in analyzed)
    unused = [f"{label}:{line} {name}" for label, line, name in unused_private_definitions(analyzed)]

    return grade_leftovers(total, unused, "private functions and classes are never used")

@rule("RULE-12-COMMENTED-OUT-CODE", "No code left in comments")
def check_commented_out_code(project):
    comments = items_in_project(project, python_comments, tree_comments)
    dead = [f"{label}:{comment.first_line}" for label, comment in comments if is_commented_out_code(comment.text, comment.language)]

    return grade_leftovers(len(comments), dead, "comments are code that was switched off")
