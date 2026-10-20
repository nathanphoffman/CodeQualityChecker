from __future__ import annotations

from typing import Callable

from .models import Project, Result, Rule, SEVERITY_WARN

_RULES: dict[str, Rule] = {}

def rule(id: str, title: str, *, language: str | None = None, framework: str | None = None,
         severity: str = SEVERITY_WARN, checkable: str = "auto", weight_multiplier: int = 1):
    def wrap(check: Callable[[Project], Result]):
        if id in _RULES:
            raise ValueError(f"duplicate rule id {id}")

        _RULES[id] = Rule(id, title, check, language, framework, severity, checkable, weight_multiplier)

        return check

    return wrap

def all_rules() -> list[Rule]:
    from . import rules  # noqa: F401  (importing registers the rules)

    return sorted(_RULES.values(), key=lambda r: r.id)
