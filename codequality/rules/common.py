from ..models import Project, Result, SEVERITY_INFO, SEVERITY_WARN
from ..registry import rule
from ..source_code import GO_TEST_SUFFIX, TYPESCRIPT_SUFFIXES
from .rule_08_few_dependencies import count_code_lines
from .rule_10_test_what_matters.limits import MAX_LINES_WITHOUT_TESTS

@rule("COMMON-001", "Project has a README", severity=SEVERITY_INFO)
def readme(project: Project) -> Result:
    found = any((project.root / name).exists() for name in ("README.md", "README", "readme.md"))

    return Result.passed() if found else Result.failed("no README found")

@rule("COMMON-002", "Project has a .gitignore", severity=SEVERITY_INFO)
def gitignore(project: Project) -> Result:
    return Result.passed() if (project.root / ".gitignore").exists() else Result.failed("no .gitignore")

@rule("COMMON-003", "Project has tests", severity=SEVERITY_WARN, checkable="partial")
def has_tests(project: Project) -> Result:
    if count_code_lines(project) < MAX_LINES_WITHOUT_TESTS:
        return Result.passed("too small to need tests")

    names = ("tests", "test", "__tests__", "spec")

    if any((project.root / name).is_dir() for name in names):
        return Result.passed()

    if any(".test." in source_file.name or ".spec." in source_file.name for source_file in project.files(*TYPESCRIPT_SUFFIXES)):
        return Result.passed()

    if any(source_file.name.endswith(GO_TEST_SUFFIX) for source_file in project.files(".go")):
        return Result.passed()

    return Result.failed("no tests directory or test files found")
