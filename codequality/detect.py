from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from .models import Project
from .source_code import C_LANG, CSHARP, DEOR, FORTRAN, GO, HARE, MOJO, PYTHON, REXX, RUST, TSCONFIG_FILE, TYPESCRIPT, TYPESCRIPT_SUFFIXES, read_source

RUST_FRAMEWORKS = {"axum": "axum", "actix-web": "actix", "tauri": "tauri"}
TS_FRAMEWORKS = {"react": "react", "next": "next", "express": "express", "@nestjs/core": "nest"}

IGNORE_FILE = ".codequalityignore"

def ignore_patterns(root: Path) -> tuple[list[str], dict[str, list[str]]]:
    """The project's .codequalityignore as (patterns for every rule, {pattern: rule ID prefixes}). A line is a wildcard, optionally followed by rule IDs
    (`tests RULE-09`) to skip it for those rules only. Blank lines and # comments are skipped, and a trailing / is dropped."""
    path = root / IGNORE_FILE
    everywhere: list[str] = []
    per_rule: dict[str, list[str]] = {}

    if not path.exists():
        return everywhere, per_rule

    for line in read_source(path).splitlines():
        words = line.strip().split()

        if not words or words[0].startswith("#"):
            continue

        pattern = words[0].rstrip("/")

        if len(words) == 1:
            everywhere.append(pattern)
        else:
            per_rule.setdefault(pattern, []).extend(words[1:])

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
    markers = ("pyproject.toml", "setup.py", "requirements.txt")

    if any((project.root / name).exists() for name in markers) or project.files(".py"):
        project.languages.add(PYTHON)

def _detect_deor(project: Project) -> None:
    if project.files(".deor"):
        project.languages.add(DEOR)

def _detect_c(project: Project) -> None:
    if project.files(".c", ".h"):
        project.languages.add(C_LANG)

def _detect_go(project: Project) -> None:
    if (project.root / "go.mod").exists() or project.files(".go"):
        project.languages.add(GO)

def _detect_csharp(project: Project) -> None:
    if project.files(".cs", ".csproj"):
        project.languages.add(CSHARP)

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
