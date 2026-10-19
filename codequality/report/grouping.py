from ..models import Status
from .Rule_Group import Rule_Group

GROUP_TITLES = {
    "RULE-01": "Rule 1: Power of 6s",
    "RULE-02": "Rule 2: Clear names",
    "RULE-03": "Rule 3: Simple beats clever",
    "RULE-04": "Rule 4: One job per function",
    "RULE-05": "Rule 5: Be secure",
    "COMMON": "Project basics",
    "RUST": "Rust",
    "TS": "TypeScript",
}
UNGRADED = (Status.MANUAL, Status.SKIPPED)
GRADE_CUTOFFS = ((90, "A"), (80, "B"), (70, "C"), (60, "D"))
PERCENT = 100.0


def group_key(rule_id):
    """RULE-03-LITTLE-CLEVERNESS -> RULE-03, COMMON-001 -> COMMON, TS-REACT-001 -> TS."""
    parts = rule_id.split("-")
    return "-".join(parts[:2]) if parts[0] == "RULE" else parts[0]


def group_score(entries):
    """Average of the checks in a group, weighted by severity. None when nothing could be graded."""
    graded = [(rule, result) for rule, result in entries if result.status not in UNGRADED]
    total_weight = sum(rule.weight for rule, _ in graded)
    if not total_weight:
        return None
    return sum(rule.weight * result.score for rule, result in graded) / total_weight


def group_results(results):
    """Rule_Groups with numbered rules first, then the rest."""
    entries_by_key = {}
    for rule, result in results:
        entries_by_key.setdefault(group_key(rule.id), []).append((rule, result))
    keys = sorted(entries_by_key, key=lambda key: (not key.startswith("RULE"), key))
    return [Rule_Group(key, GROUP_TITLES.get(key, key), group_score(entries_by_key[key]), entries_by_key[key]) for key in keys]


def overall_score(results):
    """Each group counts once, however many checks it has."""
    scores = [group.score for group in group_results(results) if group.score is not None]
    return PERCENT * sum(scores) / len(scores) if scores else PERCENT


def letter(score):
    """Letter grade for a 0-100 score."""
    for cutoff, grade in GRADE_CUTOFFS:
        if score >= cutoff:
            return grade
    return "F"
