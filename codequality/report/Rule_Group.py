from dataclasses import dataclass

@dataclass(frozen=True)
class Rule_Group:
    """All the checks that belong to one numbered rule in RULES.md (rule 15 is the common checks, rule 16 every language and framework)."""
    key: str  # "RULE-03", "COMMON", "LANGUAGE"
    title: str
    score: float | None  # 0.0 - 1.0, or None when every check needs a human

    entries: list  # (Rule, Result) pairs
    weight: float  # how many times this group counts in the total score
