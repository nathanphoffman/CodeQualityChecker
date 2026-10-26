from typing import NamedTuple

from ..models import Status
from ..report.grouping import PERCENT, group_results, overall_score

UNGRADED = (Status.MANUAL, Status.SKIPPED)
NO_CHANGE = 0.0005  # scores are fractions, so this is 0.05 of a percentage point: smaller than anything the report can show

class Change(NamedTuple):
    id: str
    title: str
    old: float | None  # 0.0 - 1.0, or None when the check did not exist or could not be graded then
    new: float | None

    @property
    def difference(self) -> float:
        """How much better (positive) or worse (negative) the check is now. A check that appeared or vanished counts as no change."""

        return 0.0 if self.old is None or self.new is None else self.new - self.old

    @property
    def moved(self) -> bool:
        """True when the score changed by enough to show, or the check or group exists in only one version."""

        return abs(self.difference) > NO_CHANGE or (self.old is None) != (self.new is None)

def graded_score(result):
    return None if result.status in UNGRADED else result.score

def overall_change(old_results, new_results) -> tuple[float, float]:
    """(old overall score, new overall score), each 0-100."""

    return overall_score(old_results), overall_score(new_results)

def group_changes(old_results, new_results) -> list[Change]:
    """One entry per numbered rule or language group that is in either version, worst drop first. Scores are 0-1."""
    old_groups = {group.key: group for group in group_results(old_results)}
    new_groups = {group.key: group for group in group_results(new_results)}
    keys = list(new_groups) + [key for key in old_groups if key not in new_groups]
    changes = []

    for key in keys:
        old, new = old_groups.get(key), new_groups.get(key)
        changes.append(Change(key, (new or old).title, old.score if old else None, new.score if new else None))

    return sorted(changes, key=lambda change: change.difference)

def check_changes(old_results, new_results) -> list[Change]:
    """Every check whose score moved, or that exists in only one version, worst drop first."""
    old_scores = {rule.id: (rule.title, graded_score(result)) for rule, result in old_results}
    new_scores = {rule.id: (rule.title, graded_score(result)) for rule, result in new_results}
    changes = []

    for rule_id in list(new_scores) + [key for key in old_scores if key not in new_scores]:
        title, new = new_scores.get(rule_id, (None, None))
        old_title, old = old_scores.get(rule_id, (None, None))
        change = Change(rule_id, title or old_title, old, new)

        if change.moved:
            changes.append(change)

    return sorted(changes, key=lambda change: change.difference)

def percent(score) -> float | None:
    return None if score is None else score * PERCENT
