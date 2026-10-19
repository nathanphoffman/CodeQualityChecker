"""Rule 9: Comment why, not what. Each comment gets a confidence that it explains why; the score is the average."""
from functools import partial

from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from ...source_code import PYTHON, items_in_project
from ..one_job.find_bodies import find_bodies
from . import amount_checks  # noqa: F401  (importing registers the rules)
from .extract import python_comments, tree_comments
from .judging.judge_comment import why_confidence
from .limits import LIKELY_WHAT_BELOW, MIN_COMPLEXITY_NEEDING_COMMENT

SNIPPET_LENGTH = 40

def snippet(text):
    return text if len(text) <= SNIPPET_LENGTH else text[:SNIPPET_LENGTH] + "..."

@rule("RULE-09-COMMENTS-SAY-WHY", "Comments explain why, not what")
def check_comments_say_why(project):
    # Comments on clever code are left out: rule 3 already asks them to explain how the code works.
    comments = [(label, comment) for label, comment in items_in_project(project, python_comments, tree_comments)
                if not comment.explains_clever]

    graded = [(label, comment, why_confidence(comment)) for label, comment in comments]

    if not graded:
        return Result.passed("no comments found")

    worst = sorted((entry for entry in graded if entry[2] < LIKELY_WHAT_BELOW), key=lambda entry: entry[2])
    listed = ", ".join(f'{label}:{comment.first_line} {confidence:.0%} "{snippet(comment.text)}"'
                       for label, comment, confidence in worst[:MAX_LISTED_OFFENDERS])

    message = f"{len(worst)} of {len(graded)} comments likely say what, not why: {listed}" if worst else ""

    return Result.scored(sum(confidence for _, _, confidence in graded) / len(graded), message)

def is_explained(function, comments):
    """A docstring, a comment inside the function, or a comment just above it."""
    inside = [c for c in comments if c.last_line >= function.line_number - 1 and c.first_line <= function.last_line]

    return function.has_docstring or bool(inside)

@rule("RULE-09-COMPLEX-CODE-COMMENTED", "Complicated functions have a comment or docstring")
def check_complex_code_commented(project):
    comments = {}

    for label, comment in items_in_project(project, python_comments, tree_comments):
        comments.setdefault(label, []).append(comment)

    functions = items_in_project(project, partial(find_bodies, language=PYTHON), find_bodies)

    complicated = [(label, f) for label, f in functions if f.branch_count + 1 >= MIN_COMPLEXITY_NEEDING_COMMENT]

    if not complicated:
        return Result.passed("no complicated functions found")

    bare = [(label, f) for label, f in complicated if not is_explained(f, comments.get(label, []))]
    listed = ", ".join(f"{label}:{f.line_number} {f.name}" for label, f in bare[:MAX_LISTED_OFFENDERS])
    message = f"{len(bare)} of {len(complicated)} complicated functions have no comment: {listed}" if bare else ""

    return Result.scored(1 - len(bare) / len(complicated), message)
