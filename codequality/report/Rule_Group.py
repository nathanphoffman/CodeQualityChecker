from dataclasses import dataclass

@dataclass(frozen=True)
class Rule_Group:
    """All the checks that belong to one numbered rule in RULES.md (or to one language or the common checks)."""
    key: str  # "RULE-03", "COMMON", "RUST", ...
    title: str
    score: float | None  # 0.0 - 1.0, or None when every check needs a human

    entries: list  # (Rule, Result) pairs
