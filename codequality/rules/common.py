from ..models import Project, Result
from ..registry import rule


@rule("COMMON-001", "Project has a README", severity="info")
def readme(p: Project) -> Result:
    found = any((p.root / n).exists() for n in ("README.md", "README", "readme.md"))
    return Result.passed() if found else Result.failed("no README found")


@rule("COMMON-002", "Project has a .gitignore", severity="info")
def gitignore(p: Project) -> Result:
    return Result.passed() if (p.root / ".gitignore").exists() else Result.failed("no .gitignore")


@rule("COMMON-003", "Project has tests", severity="warn", checkable="partial")
def has_tests(p: Project) -> Result:
    names = ("tests", "test", "__tests__", "spec")
    if any((p.root / n).is_dir() for n in names):
        return Result.passed()
    if any(".test." in f.name or ".spec." in f.name for f in p.files(".ts", ".tsx")):
        return Result.passed()
    return Result.failed("no tests directory or test files found")
