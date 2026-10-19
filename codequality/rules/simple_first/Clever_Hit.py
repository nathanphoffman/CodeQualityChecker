from dataclasses import dataclass


@dataclass(frozen=True)
class Clever_Hit:
    kind: str
    label: str  # "file:line"
    explained: bool
