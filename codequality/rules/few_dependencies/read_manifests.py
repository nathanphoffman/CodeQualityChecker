import json
import tomllib

from ...source_code import read_source

PYTHON_PACKAGE, NPM_PACKAGE, RUST_CRATE = "pip", "npm", "cargo"
DEPENDENCIES = "dependencies"
PYTHON_CORE_NAME = "python"  # Poetry lists the Python version among its dependencies


def package_name(requirement):
    """`tree-sitter>=0.25,<0.27` -> `tree-sitter`. Names compare equal however - _ and . are written."""
    name = ""
    for character in requirement.strip():
        if not (character.isalnum() or character in "-_."):
            break
        name += character
    return name.lower().replace("_", "-").replace(".", "-")


def python_dependencies(project):
    """Runtime dependencies from pyproject.toml (PEP 621 or Poetry) and requirements.txt."""
    found = set()
    pyproject = project.root / "pyproject.toml"
    if pyproject.exists():
        data = tomllib.loads(read_source(pyproject))
        found |= {package_name(spec) for spec in data.get("project", {}).get(DEPENDENCIES, [])}
        found |= set(data.get("tool", {}).get("poetry", {}).get(DEPENDENCIES, {})) - {PYTHON_CORE_NAME}
    requirements = project.root / "requirements.txt"
    if requirements.exists():
        lines = [line.strip() for line in read_source(requirements).splitlines()]
        found |= {package_name(line) for line in lines if line and not line.startswith(("#", "-"))}
    return {(PYTHON_PACKAGE, name) for name in found}


def table_dependencies(project, filename, load, ecosystem):
    """Names in the "dependencies" table of a manifest file that `load` can read (JSON or TOML)."""
    path = project.root / filename
    if not path.exists():
        return set()
    return {(ecosystem, name) for name in load(read_source(path)).get(DEPENDENCIES, {})}


def project_dependencies(project):
    """{(where it comes from, name)} for every direct runtime dependency. Dev-only tools are not counted."""
    node = table_dependencies(project, "package.json", json.loads, NPM_PACKAGE)
    return python_dependencies(project) | node | table_dependencies(project, "Cargo.toml", tomllib.loads, RUST_CRATE)
