"""Rule 3: Simple beats clever. Clever code is allowed, but it must be rare and explained."""
from collections import Counter

from ...models import MAX_LISTED_OFFENDERS, Result
from ...registry import rule
from .find_clever import scan_project
from .limits import LINES_PER_DENSITY_UNIT, MAX_CLEVER_PER_100_LINES


def describe_unexplained(unexplained):
    listed = ", ".join(f"{hit.label} {hit.kind}" for hit in unexplained[:MAX_LISTED_OFFENDERS])
    return f"{len(unexplained)} clever constructs have no comment: {listed}" if unexplained else ""


@rule("RULE-03-CLEVER-IS-EXPLAINED", "Clever code has a comment explaining how it works")
def check_clever_is_explained(project):
    hits, _ = scan_project(project)
    if not hits:
        return Result.passed("no clever code found")
    unexplained = [hit for hit in hits if not hit.explained]
    return Result.scored(1 - len(unexplained) / len(hits), describe_unexplained(unexplained))


@rule("RULE-03-LITTLE-CLEVERNESS", "Clever constructs are rare")
def check_cleverness_amount(project):
    hits, line_count = scan_project(project)
    if not hits:
        return Result.passed("no clever code found")
    per_hundred = len(hits) * LINES_PER_DENSITY_UNIT / line_count
    kind_counts = Counter([hit.kind for hit in hits]).most_common()
    kinds = ", ".join([f"{kind} ({count})" for kind, count in kind_counts])
    return Result.scored(1 - per_hundred / MAX_CLEVER_PER_100_LINES, f"{len(hits)} in {line_count} lines: {kinds}")
