from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Project

RUST_FRAMEWORKS = {"axum": "axum", "actix-web": "actix", "tauri": "tauri"}
TS_FRAMEWORKS = {"react": "react", "next": "next", "express": "express", "@nestjs/core": "nest"}


def detect(root: Path) -> Project:
    project = Project(root=root)
    _detect_python(project)
    _detect_rust(project)
    _detect_ts(project)
    return project


def _detect_python(project: Project) -> None:
    markers = ("pyproject.toml", "setup.py", "requirements.txt")
    if any((project.root / name).exists() for name in markers) or project.files(".py"):
        project.languages.add("python")


def _detect_rust(project: Project) -> None:
    cargo = project.root / "Cargo.toml"
    if not cargo.exists():
        return
    project.languages.add("rust")
    text = cargo.read_text(errors="ignore")
    for crate, name in RUST_FRAMEWORKS.items():
        # finds a line starting with the crate name followed by "=" or "." (a Cargo.toml dependency entry)
        if re.search(rf"^\s*{re.escape(crate)}\s*[=.]", text, re.M):
            project.frameworks.add(name)


def _detect_ts(project: Project) -> None:
    pkg = project.root / "package.json"
    if not pkg.exists() and not (project.root / "tsconfig.json").exists():
        return
    if (project.root / "tsconfig.json").exists() or project.files(".ts", ".tsx"):
        project.languages.add("typescript")
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text())
        except json.JSONDecodeError:
            return
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        for dep, name in TS_FRAMEWORKS.items():
            if dep in deps:
                project.frameworks.add(name)
