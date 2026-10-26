"""Shared pieces for the language and framework checks: look for a pattern in a project's real code and turn what is found into a Result."""
from pathlib import Path

from ..models import MAX_LISTED_OFFENDERS, Project, Result
from ..source_code import line_number_at, non_test_files, read_source

def pattern_hits(project: Project, suffixes: tuple, pattern) -> list[str]:
    """'file:line' for every match of the compiled pattern in the non-test files with these suffixes."""
    hits = []

    for path in non_test_files(project, suffixes):
        text = read_source(path)
        hits += [f"{project.label_for(path)}:{line_number_at(text, match.start())}" for match in pattern.finditer(text)]

    return hits

def fail_on_hits(hits: list[str], problem: str) -> Result:
    """Passes when nothing was found. Otherwise fails and lists the first few places."""

    if not hits:
        return Result.passed()

    return Result.failed(f"{problem}: {', '.join(hits[:MAX_LISTED_OFFENDERS])}")

def fail_unless_found(project: Project, suffixes: tuple, pattern, missing: str) -> Result:
    """Passes when the pattern appears anywhere in the non-test files with these suffixes, otherwise fails with `missing`."""
    texts = (read_source(path) for path in non_test_files(project, suffixes))

    return Result.passed() if any(pattern.search(text) for text in texts) else Result.failed(missing)

def config_files_found(project: Project, names: tuple) -> list[str]:
    """Which of these file names sit in the project root."""

    return [name for name in names if (project.root / name).exists()]

def config_mentions(project: Project, names: tuple, markers: tuple) -> list[str]:
    """Which of these root files exist and hold one of the markers in their text, like `[tool.ruff` in pyproject.toml."""
    paths = [project.root / name for name in names if (project.root / name).exists()]

    # two loops: every existing file paired with every marker, kept when the marker is in the file
    return [path.name for path in paths if any(marker in read_source(path) for marker in markers)]

def named_file_hits(project: Project, file_names: tuple, pattern) -> list[str]:
    """'file:line' for every match of the pattern in the project files with one of these exact names, like tauri.conf.json."""
    hits = []

    for path in project.files(*{Path(name).suffix for name in file_names}):
        text = read_source(path) if path.name in file_names else ""
        hits += [f"{project.label_for(path)}:{line_number_at(text, match.start())}" for match in pattern.finditer(text)]

    return hits
