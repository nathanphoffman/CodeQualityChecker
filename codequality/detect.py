from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from .models import Project
from .source_code import C_LANG, CSHARP, DEOR, FORTRAN, GO, HARE, MOJO, PYTHON, REXX, RUST, TSCONFIG_FILE, TYPESCRIPT, TYPESCRIPT_SUFFIXES, read_source

RUST_FRAMEWORKS = {"axum": "axum", "actix-web": "actix", "tauri": "tauri"}
TS_FRAMEWORKS = {"react": "react", "next": "next", "express": "express", "@nestjs/core": "nest"}
PYTHON_FRAMEWORKS = {"django": "django", "flask": "flask", "fastapi": "fastapi"}
PYTHON_DEPENDENCY_FILES = ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")
GO_FRAMEWORKS = {"github.com/gin-gonic/gin": "gin", "github.com/labstack/echo": "echo", "github.com/gofiber/fiber": "fiber"}
CSHARP_FRAMEWORKS = {"Microsoft.NET.Sdk.Web": "aspnet", "Microsoft.AspNetCore": "aspnet", "Microsoft.EntityFrameworkCore": "efcore",
                     "Microsoft.AspNetCore.Components": "blazor", "Microsoft.NET.Sdk.BlazorWebAssembly": "blazor"}

IGNORE_FILE = ".codequalityignore"

def ignore_lines(root: Path) -> list[list[str]]:
    """The words on each meaningful line of the project's .codequalityignore. Blank lines and # comments are skipped."""
    path = root / IGNORE_FILE

    if not path.exists():
        return []

    words_by_line = [line.split() for line in read_source(path).splitlines()]

    return [words for words in words_by_line if words and not words[0].startswith("#")]

def ignore_patterns(root: Path) -> tuple[list[str], dict[str, list[str]]]:
    """The project's .codequalityignore as (patterns for every rule, {pattern: rule ID prefixes}). A line is a wildcard, optionally followed by rule IDs
    (`tests RULE-09`) to skip it for those rules only. A trailing / on the wildcard is dropped."""
    everywhere: list[str] = []
    per_rule: dict[str, list[str]] = {}

    for pattern, *rule_ids in ignore_lines(root):
        if rule_ids:
            per_rule.setdefault(pattern.rstrip("/"), []).extend(rule_ids)
        else:
            everywhere.append(pattern.rstrip("/"))

    return everywhere, per_rule

def detect(root: Path, exclude: list[str] | None = None) -> Project:
    everywhere, per_rule = ignore_patterns(root)
    project = Project(root=root, exclude=(exclude or []) + everywhere, rule_exclude=per_rule)
    _detect_python(project)
    _detect_rust(project)
    _detect_ts(project)
    _detect_deor(project)
    _detect_hare(project)
    _detect_c(project)
    _detect_go(project)
    _detect_csharp(project)
    _detect_mojo(project)
    _detect_fortran(project)
    _detect_rexx(project)

    return project

def _detect_python(project: Project) -> None:
    """Python when a Python project file or any .py file exists; frameworks are then read from the dependency files."""
    markers = ("pyproject.toml", "setup.py", "requirements.txt")

    if any((project.root / name).exists() for name in markers) or project.files(".py"):
        project.languages.add(PYTHON)
        _detect_python_frameworks(project)

def _detect_python_frameworks(project: Project) -> None:
    paths = [project.root / name for name in PYTHON_DEPENDENCY_FILES if (project.root / name).exists()]
    text = "\n".join(read_source(path) for path in paths)

    for package, framework in PYTHON_FRAMEWORKS.items():
        # finds the package name at the start of a line or after a quote or space, so `flask-cors` and `my-django-tools` don't count as the framework
        if re.search(rf"(^|[\"'\s])({package})(?![\w-])", text, re.I | re.M):
            project.frameworks.add(framework)

def _detect_deor(project: Project) -> None:
    if project.files(".deor"):
        project.languages.add(DEOR)

def _detect_c(project: Project) -> None:
    if project.files(".c", ".h"):
        project.languages.add(C_LANG)

def _detect_go(project: Project) -> None:
    """Go when go.mod or any .go file exists; frameworks are named by the modules go.mod requires."""

    if (project.root / "go.mod").exists() or project.files(".go"):
        project.languages.add(GO)

    go_mod = project.root / "go.mod"
    text = read_source(go_mod) if go_mod.exists() else ""
    project.frameworks.update(name for module, name in GO_FRAMEWORKS.items() if module in text)

def _detect_csharp(project: Project) -> None:
    """C# when any .cs or .csproj file exists; frameworks are named by the SDK or packages in the .csproj files."""

    if project.files(".cs", ".csproj"):
        project.languages.add(CSHARP)

    project_text = "\n".join(read_source(path) for path in project.files(".csproj"))
    project.frameworks.update(name for marker, name in CSHARP_FRAMEWORKS.items() if marker in project_text)

def _detect_mojo(project: Project) -> None:
    if project.files(".mojo", ".🔥"):
        project.languages.add(MOJO)

def _detect_rexx(project: Project) -> None:
    if project.files(".rexx", ".rex", ".exec"):
        project.languages.add(REXX)

def _detect_fortran(project: Project) -> None:
    if project.files(".f90", ".F90", ".f95", ".f03", ".f08"):
        project.languages.add(FORTRAN)

def _detect_hare(project: Project) -> None:
    if project.files(".ha"):
        project.languages.add(HARE)

def _detect_rust(project: Project) -> None:
    cargo = project.root / "Cargo.toml"

    if not cargo.exists():
        return

    project.languages.add(RUST)
    text = read_source(cargo)

    for crate, name in RUST_FRAMEWORKS.items():
        # finds a line starting with the crate name followed by "=" or "." (a Cargo.toml dependency entry)
        if re.search(rf"^\s*{re.escape(crate)}\s*[=.]", text, re.M):
            project.frameworks.add(name)

def _detect_ts(project: Project) -> None:
    package_json = project.root / "package.json"

    if not package_json.exists() and not (project.root / TSCONFIG_FILE).exists():
        return

    if (project.root / TSCONFIG_FILE).exists() or project.files(*TYPESCRIPT_SUFFIXES):
        project.languages.add(TYPESCRIPT)

    if package_json.exists():
        try:
            data = json.loads(read_source(package_json))
        except json.JSONDecodeError as error:
            warnings.warn(f"skipped framework detection: {package_json} is not valid JSON ({error})")

            return

        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

        for dependency, name in TS_FRAMEWORKS.items():
            if dependency in deps:
                project.frameworks.add(name)
