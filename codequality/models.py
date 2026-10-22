from __future__ import annotations

from dataclasses import dataclass, field
import subprocess
from enum import Enum
from fnmatch import fnmatch
from functools import lru_cache
from pathlib import Path
from typing import Callable

IGNORED_FOLDERS = {"node_modules", "target", ".git", "dist", "build", ".next", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
                   "obj"}  # obj is where .NET puts generated code
MAX_LISTED_OFFENDERS = 5
SEVERITY_ERROR, SEVERITY_WARN, SEVERITY_INFO = "error", "warn", "info"
SEVERITY_WEIGHTS = {SEVERITY_ERROR: 3, SEVERITY_WARN: 2, SEVERITY_INFO: 1}
CHECK_AUTO, CHECK_PARTIAL, CHECK_MANUAL = "auto", "partial", "manual"

@lru_cache(maxsize=None)
def git_ignored_paths(root: Path) -> frozenset[str]:
    """Paths (relative to root) that .gitignore hides. A wholly ignored folder is listed once. Empty when root is not a git repo."""
    command = ["git", "-C", str(root), "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"]

    try:
        listing = subprocess.run(command, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return frozenset()  # no git, or not a repo: only the built-in ignore list applies

    return frozenset(path.rstrip("/") for path in listing.split("\0") if path)

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
    languages: set[str] = field(default_factory=set)  # "rust", "typescript", "hare"
    frameworks: set[str] = field(default_factory=set)  # "axum", "react", ...
    exclude: list[str] = field(default_factory=list)  # wildcard patterns, e.g. "*out.rs*", matched against names and relative paths
    _remembered: dict = field(default_factory=dict, repr=False)  # answers to slow questions, so each is worked out once per run

    def label_for(self, path) -> str:
        return str(Path(path).relative_to(self.root))

    def remember(self, key, compute):
        """The result of compute(), worked out the first time this key is asked for. Callers must not change what they get."""

        if key not in self._remembered:
            self._remembered[key] = compute()

        return self._remembered[key]

    def is_ignored(self, path) -> bool:
        """True for build/vendor folders, anything .gitignore hides (or sits inside something it hides), and anything (or anything inside a folder) matching an --exclude pattern or a line of .codequalityignore."""
        parts = Path(path).relative_to(self.root).parts
        hidden = git_ignored_paths(self.root)

        if any(fnmatch(part, pattern) or fnmatch("/".join(parts[:end]), pattern) for end, part in enumerate(parts, start=1) for pattern in self.exclude):
            return True

        return bool(IGNORED_FOLDERS & set(parts)) or any("/".join(parts[:end]) in hidden for end in range(1, len(parts) + 1))

    def files(self, *suffixes: str) -> list[Path]:
        """Source files under root, skipping build/vendor dirs and gitignored files."""
        found = self.remember(("files", suffixes), lambda: [path for path in self.root.rglob("*") if path.is_file() and path.suffix in suffixes and not self.is_ignored(path)])

        return list(found)

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
