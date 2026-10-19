from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable

IGNORED_FOLDERS = {"node_modules", "target", ".git", "dist", "build", ".next", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
MAX_LISTED_OFFENDERS = 5
SEVERITY_ERROR, SEVERITY_WARN, SEVERITY_INFO = "error", "warn", "info"
SEVERITY_WEIGHTS = {SEVERITY_ERROR: 3, SEVERITY_WARN: 2, SEVERITY_INFO: 1}
CHECK_AUTO, CHECK_PARTIAL, CHECK_MANUAL = "auto", "partial", "manual"

class Status(str, Enum):
    PASS = "pass"
    PARTIAL = "partial"
    FAIL = "fail"
    MANUAL = "manual"  # can't be checked by code, needs a human
    SKIPPED = "skipped"

@dataclass
class Result:
    status: Status
    score: float = 0.0  # 0.0 - 1.0, ignored for MANUAL/SKIPPED
    message: str = ""

    @classmethod
    def passed(cls, message: str = "") -> Result:
        return cls(Status.PASS, 1.0, message)

    @classmethod
    def failed(cls, message: str = "") -> Result:
        return cls(Status.FAIL, 0.0, message)

    @classmethod
    def scored(cls, score: float, message: str = "") -> Result:
        score = max(0.0, min(1.0, score))
        status = Status.PARTIAL

        if score >= 1.0:
            status = Status.PASS
        elif score <= 0.0:
            status = Status.FAIL

        return cls(status, score, message)

    @classmethod
    def manual(cls, message: str = "") -> Result:
        return cls(Status.MANUAL, 0.0, message)

@dataclass
class Project:
    root: Path
    languages: set[str] = field(default_factory=set)  # "rust", "typescript"
    frameworks: set[str] = field(default_factory=set)  # "axum", "react", ...

    def label_for(self, path) -> str:
        return str(Path(path).relative_to(self.root))

    def files(self, *suffixes: str) -> list[Path]:
        """Source files under root, skipping build/vendor dirs."""
        out = []

        for p in self.root.rglob("*"):
            if p.is_file() and p.suffix in suffixes and not IGNORED_FOLDERS & set(p.relative_to(self.root).parts):
                out.append(p)

        return out

@dataclass
class Rule:
    id: str
    title: str
    check: Callable[[Project], Result]
    language: str | None = None  # None = all languages

    framework: str | None = None  # None = any
    severity: str = SEVERITY_WARN
    checkable: str = CHECK_AUTO
    weight_multiplier: int = 1  # a check that stands in for several counts that many times

    @property
    def weight(self) -> int:
        return SEVERITY_WEIGHTS[self.severity] * self.weight_multiplier

    def applies_to(self, project: Project) -> bool:
        if self.language and self.language not in project.languages:
            return False

        if self.framework and self.framework not in project.frameworks:
            return False

        return True
