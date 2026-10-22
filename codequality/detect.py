from __future__ import annotations

import json
import re
import warnings
from pathlib import Path

from .models import Project
from .source_code import DEOR, HARE, PYTHON, RUST, TSCONFIG_FILE, TYPESCRIPT, TYPESCRIPT_SUFFIXES, read_source

RUST_FRAMEWORKS = {"axum": "axum", "actix-web": "actix", "tauri": "tauri"}
TS_FRAMEWORKS = {"react": "react", "next": "next", "express": "express", "@nestjs/core": "nest"}

def detect(root: Path, exclude: list[str] | None = None) -> Project:
    project = Project(root=root, exclude=exclude or [])
    _detect_python(project)
    _detect_rust(project)
    _detect_ts(project)
    _detect_deor(project)
    _detect_hare(project)

    return project

def _detect_python(project: Project) -> None:
    markers = ("pyproject.toml", "setup.py", "requirements.txt")

    if any((project.root / name).exists() for name in markers) or project.files(".py"):
        project.languages.add(PYTHON)

def _detect_deor(project: Project) -> None:
    if project.files(".deor"):
        project.languages.add(DEOR)

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
