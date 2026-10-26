"""Every language with a standard formatter or linter should have it configured. RUST-002 and TS-003 cover Rust and TypeScript."""
from ..models import SEVERITY_WARN, Project, Result
from ..registry import rule
from ..source_code import C_LANG, CSHARP, FORTRAN, GO, PYTHON
from .check_helpers import config_files_found, config_mentions

PYTHON_CONFIG_FILES = ("ruff.toml", ".ruff.toml", ".flake8", ".pylintrc", "pylintrc", ".style.yapf")
PYTHON_SHARED_FILES = ("pyproject.toml", "setup.cfg", "tox.ini")  # these hold many tools' settings, so they only count with a tool's section in them
PYTHON_TOOL_SECTIONS = ("[tool.ruff", "[tool.black", "[tool.flake8", "[tool.pylint", "[tool.yapf", "[flake8]", "[pylint", "[yapf]")

GO_CONFIG_FILES = (".golangci.yml", ".golangci.yaml", ".golangci.toml", ".golangci.json")
C_CONFIG_FILES = (".clang-format", ".clang-tidy")  # a formatter and a linter, so each counts half
CSHARP_CONFIG_FILES = (".editorconfig", ".globalconfig", "stylecop.json")
FORTRAN_CONFIG_FILES = (".fprettify.rc", "fprettify.rc", ".fortitude.toml", "fortitude.toml")

def configured(found_files: list, advice: str) -> Result:
    return Result.passed() if found_files else Result.failed(advice)

@rule("PYTHON-001", "Formatter / linter configured (ruff, black, flake8, pylint)", language=PYTHON, severity=SEVERITY_WARN)
def python_tools(project: Project) -> Result:
    found = config_files_found(project, PYTHON_CONFIG_FILES) or config_mentions(project, PYTHON_SHARED_FILES, PYTHON_TOOL_SECTIONS)

    return configured(found, "no ruff, black, flake8, pylint or yapf settings found")

@rule("GO-001", "Linter configured (golangci-lint)", language=GO, severity=SEVERITY_WARN)
def go_linter(project: Project) -> Result:
    return configured(config_files_found(project, GO_CONFIG_FILES), "no .golangci config file")

@rule("C-001", "clang-format / clang-tidy configured", language=C_LANG, severity=SEVERITY_WARN, checkable="partial")
def c_tools(project: Project) -> Result:
    found = len(config_files_found(project, C_CONFIG_FILES))

    return Result.scored(found / len(C_CONFIG_FILES), f"{found}/{len(C_CONFIG_FILES)} config files found")

@rule("CSHARP-001", "Code style configured (.editorconfig)", language=CSHARP, severity=SEVERITY_WARN)
def csharp_style(project: Project) -> Result:
    return configured(config_files_found(project, CSHARP_CONFIG_FILES), "no .editorconfig, .globalconfig or stylecop.json")

@rule("FORTRAN-001", "Formatter / linter configured (fprettify, fortitude)", language=FORTRAN, severity=SEVERITY_WARN)
def fortran_tools(project: Project) -> Result:
    return configured(config_files_found(project, FORTRAN_CONFIG_FILES), "no fprettify or fortitude config file")
