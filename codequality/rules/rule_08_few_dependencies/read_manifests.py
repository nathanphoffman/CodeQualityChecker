import json
import re
import tomllib

from ...source_code import read_source

PYTHON_PACKAGE, NPM_PACKAGE, RUST_CRATE, GO_MODULE, FPM_PACKAGE, PIXI_PACKAGE, NUGET_PACKAGE = "pip", "npm", "cargo", "go", "fpm", "pixi", "nuget"
DEPENDENCIES = "dependencies"
PYTHON_CORE_NAME = "python"  # Poetry lists the Python version among its dependencies
MOJO_TOOLCHAIN = {"max", "mojo", "modular", "python"}  # pixi lists the compiler itself among its dependencies
PACKAGE_REFERENCE = re.compile(r'<PackageReference\s+(?:[^>]*?\s)?Include="([^"]+)"')  # a NuGet dependency in a .csproj file
NUGET_TEST_TOOLS = {"Microsoft.NET.Test.Sdk", "xunit", "xunit.runner.visualstudio", "xunit.analyzers", "NUnit", "NUnit3TestAdapter", "MSTest.TestAdapter",
                    "MSTest.TestFramework", "coverlet.collector", "coverlet.msbuild"}  # only used to run tests, so not counted

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

def go_dependencies(project):
    """Modules in go.mod's `require` lines, one-line or in a ( ) block. Ones marked `// indirect` are pulled in by others."""
    path = project.root / "go.mod"
    found, in_block = set(), False

    if not path.exists():
        return found

    for line in read_source(path).splitlines():
        text = line.strip()
        in_block = in_block or text == "require ("

        if text == ")":
            in_block = False
        elif in_block or text.startswith("require "):
            fields = text.removeprefix("require ").split()
            found |= {(GO_MODULE, fields[0])} if fields and "// indirect" not in text and fields[0] != "require" else set()

    return found

def nuget_dependencies(project):
    """Packages named in every .csproj file, without the packages that only run the tests."""
    found = set()

    for path in project.files(".csproj"):
        found |= {(NUGET_PACKAGE, name) for name in PACKAGE_REFERENCE.findall(read_source(path)) if name not in NUGET_TEST_TOOLS}

    return found

def project_dependencies(project):
    """{(where it comes from, name)} for every direct runtime dependency. Dev-only tools are not counted."""
    node = table_dependencies(project, "package.json", json.loads, NPM_PACKAGE)

    # the entries of every pixi manifest that exists
    pixi = {entry for filename in ("pixi.toml", "mojoproject.toml") for entry in table_dependencies(project, filename, tomllib.loads, PIXI_PACKAGE)}

    return (python_dependencies(project) | node | table_dependencies(project, "Cargo.toml", tomllib.loads, RUST_CRATE) | go_dependencies(project)
            | table_dependencies(project, "fpm.toml", tomllib.loads, FPM_PACKAGE) | nuget_dependencies(project) | {entry for entry in pixi if entry[1] not in MOJO_TOOLCHAIN})
