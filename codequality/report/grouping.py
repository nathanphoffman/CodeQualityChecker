from ..models import Status
from .Rule_Group import Rule_Group

LANGUAGE_GROUP = "LANGUAGE"

# The numbered rules in RULES.md order. A group's position here is its rule number, and it sets the group's weight.
# The keys still use the older ids, so RULE-04 (one job) now sits in position 8.
GROUP_NAMES = (
    ("RULE-01", "Power of 6s"),
    ("RULE-02", "Clear names"),
    ("RULE-03", "Simple beats clever"),
    ("RULE-05", "Be secure"),
    ("RULE-06", "Don't repeat yourself"),
    ("RULE-07", "No magic numbers"),
    ("RULE-08", "Minimize dependencies"),
    ("RULE-04", "One job per function"),
    ("RULE-09", "Add comments"),
    ("RULE-10", "Test what matters"),
    ("RULE-11", "Fail loudly"),
    ("RULE-12", "Clean up"),
    ("RULE-13", "Keep the project small"),
    ("RULE-14", "Space it out"),
    ("COMMON", "Project basics"),
    (LANGUAGE_GROUP, "Language/Framework best practices"),
)
GROUP_POSITIONS = {key: position for position, (key, _) in enumerate(GROUP_NAMES, 1)}
GROUP_TITLES = {key: f"Rule {GROUP_POSITIONS[key]}: {name}" for key, name in GROUP_NAMES}

# Rule 1 counts fully in the total and the last rule counts 1/8 as much, with the rules between falling in a straight line.
LAST_RULE_WEIGHT = 1 / 8

UNGRADED = (Status.MANUAL, Status.SKIPPED)
GRADE_CUTOFFS = ((90, "A"), (80, "B"), (70, "C"), (60, "D"))
PERCENT = 100.0

# Inside a 10-point band, the bottom three points (_0 to _2) get a minus and the top two (_8 and _9, and 100) get a plus.
MINUS_BELOW_POINT, PLUS_FROM_POINT = 3, 8

def group_key(rule_id):
    """RULE-03-LITTLE-CLEVERNESS -> RULE-03, COMMON-001 -> COMMON, and every language or framework check (TS-REACT-001) -> LANGUAGE."""
    parts = rule_id.split("-")

    if parts[0] == "RULE":
        return "-".join(parts[:2])

    return parts[0] if parts[0] == "COMMON" else LANGUAGE_GROUP

def weight_text(group):
    """The group's multiplier for display, like x0.875."""

    return f"x{group.weight:.3f}"

def group_weight(key):
    """How many times the group counts in the total score: earlier rules count more."""

    share_of_the_way_down = (GROUP_POSITIONS[key] - 1) / (len(GROUP_NAMES) - 1)

    return 1 - share_of_the_way_down * (1 - LAST_RULE_WEIGHT)

def group_score(entries):
    """Average of the checks in a group, weighted by severity. None when nothing could be graded."""
    graded = [(rule, result) for rule, result in entries if result.status not in UNGRADED]
    total_weight = sum(rule.weight for rule, _ in graded)

    if not total_weight:
        return None

    return sum(rule.weight * result.score for rule, result in graded) / total_weight

def group_results(results):
    """Rule_Groups in RULES.md order."""
    entries_by_key = {}

    for rule, result in results:
        entries_by_key.setdefault(group_key(rule.id), []).append((rule, result))

    keys = sorted(entries_by_key, key=GROUP_POSITIONS.get)

    return [Rule_Group(key, GROUP_TITLES[key], group_score(entries_by_key[key]), entries_by_key[key], group_weight(key)) for key in keys]

def overall_score(results):
    """Each group counts once, however many checks it has, times its weight. Groups nobody could grade are left out."""
    graded = [group for group in group_results(results) if group.score is not None]

    if not graded:
        return PERCENT

    return PERCENT * sum(group.weight * group.score for group in graded) / sum(group.weight for group in graded)

def rounded_score(percent, decimals=0):
    """A 0-100 score rounded to `decimals` places, but never up to 100 unless it is exactly 100, so one leftover problem can't read as perfect."""
    rounded = round(percent, decimals)

    return PERCENT - 10 ** -decimals if percent < PERCENT <= rounded else rounded

def shown_percent(percent, decimals=0):
    """`rounded_score` as text, like 94.6 or 99.9."""

    return f"{rounded_score(percent, decimals):.{decimals}f}"

def grade_sign(points_into_band):
    """"-" for the bottom of a band, "+" for the top, nothing between."""

    if points_into_band < MINUS_BELOW_POINT:
        return "-"

    return "+" if points_into_band >= PLUS_FROM_POINT else ""

def letter(score):
    """Letter grade for a 0-100 score, like B+ or C-. F has no sign."""

    for cutoff, grade in GRADE_CUTOFFS:
        if score >= cutoff:
            return grade + grade_sign(score - cutoff)

    return "F"
