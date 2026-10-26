import re
from pathlib import PurePosixPath
from typing import NamedTuple

from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.tree_walk import walk
from ....source_code import NAME_GROUP, TYPESCRIPT, TYPESCRIPT_SUFFIXES, non_test_files, read_source

# Files a framework or build tool loads by name, so nothing imports what they export.
ENTRY_FILE_STEMS = {"page", "layout", "route", "loading", "error", "not-found", "template", "middleware", "main", "vite-env.d"}
ENTRY_FILE_MARKERS = (".config.", ".stories.", ".d.ts")

# Clever on purpose: `import("./path")`, written for code that loads a file only when needed, with the path in a group called "name".
DYNAMIC_IMPORT = re.compile(rf"""\bimport\(\s*["'](?P<{NAME_GROUP}>[^"']+)["']\s*\)""")

EXPORTED_KINDS = {"function_declaration", "generator_function_declaration", "class_declaration"}
FUNCTION_VALUES = {"arrow_function", "function_expression"}

class Export(NamedTuple):
    name: str
    line: int
    is_default: bool

class Usage(NamedTuple):
    names: set  # names imported or re-exported by name
    default_modules: set  # modules loaded for their default export
    whole_modules: set  # modules loaded as a whole: `import * as`, `export *`, `import()`

def module_key(path_text):
    """A module as its last folder or file name: `./panels/Slider` and `../Slider.tsx` are both `Slider`. An index file is its folder."""
    path = PurePosixPath(path_text)
    stem = path.name.rsplit(".", 1)[0] if path.suffix in TYPESCRIPT_SUFFIXES else path.name

    return path.parent.name if stem == "index" else stem

def exported_names(statement):
    """The functions, components and classes one `export` statement declares."""
    declaration = statement.child_by_field_name("declaration")
    is_default = any(child.type == "default" for child in statement.children)

    if declaration is None:
        return []

    if declaration.type in EXPORTED_KINDS:
        name = declaration.child_by_field_name("name")

        return [Export(name.text.decode(), name.start_point.row + 1, is_default)] if name else []

    declarators = [node for node in declaration.named_children if node.type == "variable_declarator"]
    values = [(node.child_by_field_name("name"), node.child_by_field_name("value")) for node in declarators]

    return [Export(name.text.decode(), name.start_point.row + 1, False) for name, value in values if value is not None and value.type in FUNCTION_VALUES]

def string_text(node):
    return node.text.decode().strip("\"'") if node is not None else None

def read_export(statement, usage):
    """A re-export (`export { a } from "./x"`) uses those names; `export * from` uses the whole module."""
    module = string_text(statement.child_by_field_name("source"))

    if module is None:
        return

    specifiers = [node for node in walk(statement) if node.type == "export_specifier"]

    if specifiers:
        usage.names.update(node.child_by_field_name("name").text.decode() for node in specifiers)
    else:
        usage.whole_modules.add(module_key(module))

def read_import(statement, usage):
    module = module_key(string_text(statement.child_by_field_name("source")) or "")

    for node in walk(statement):
        if node.type == "import_specifier":
            usage.names.add(node.child_by_field_name("name").text.decode())
        elif node.type == "namespace_import":
            usage.whole_modules.add(module)
        elif node.type == "import_clause" and any(child.type == "identifier" for child in node.children):
            usage.default_modules.add(module)

def read_file(source, usage):
    """The exports in one file's source, after adding what the file imports to `usage`."""
    root = parse_tree(source, TYPESCRIPT)
    exports = []

    for statement in root.named_children:
        if statement.type == "import_statement":
            read_import(statement, usage)
        elif statement.type == "export_statement":
            read_export(statement, usage)
            exports += exported_names(statement)

    usage.whole_modules.update(module_key(match.group(NAME_GROUP)) for match in DYNAMIC_IMPORT.finditer(source))

    return exports

def is_entry_file(path):
    return path.stem in ENTRY_FILE_STEMS or any(marker in path.name for marker in ENTRY_FILE_MARKERS)

def unused_exports(project):
    """(total exports, ["file:line name"]) for exported functions, components and classes that nothing imports.
    Tests count as importers, but their own exports are not judged."""
    usage = Usage(set(), set(), set())
    exports = {}

    for path in project.files(*TYPESCRIPT_SUFFIXES):
        exports[path] = read_file(read_source(path), usage)

    judged = [path for path in non_test_files(project, TYPESCRIPT_SUFFIXES) if not is_entry_file(path)]
    unused = []
    total = 0

    for path in judged:
        key = module_key(str(path))

        for export in exports[path]:
            total += 1
            used = export.name in usage.names or key in usage.whole_modules or (export.is_default and key in usage.default_modules)
            unused += [] if used else [f"{project.label_for(path)}:{export.line} {export.name}"]

    return total, unused
