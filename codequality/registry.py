from __future__ import annotations

from typing import Callable

from .models import Project, Result, Rule

_RULES: dict[str, Rule] = {}

def rule(id: str, title: str, **options):
    """Registers a check. `options` are the optional Rule fields: language, framework, severity, checkable, weight_multiplier."""
    def wrap(check: Callable[[Project], Result]):
        if id in _RULES:
            raise ValueError(f"duplicate rule id {id}")

        _RULES[id] = Rule(id, title, check, **options)

        return check

    return wrap

def all_rules() -> list[Rule]:
    from . import rules  # noqa: F401  (importing registers the rules)

    return sorted(_RULES.values(), key=lambda r: r.id)
