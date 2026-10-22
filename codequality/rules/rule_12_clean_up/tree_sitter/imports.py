import re

from ....source_code import GO, HARE, RUST
from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.limits import NOQA_MARKER
from .names import IMPORT_TYPES, counts_outside_imports

PUBLIC_MARKER = "visibility_modifier"  # `pub use` re-exports on purpose

def typescript_bound_names(statement):
    """Names from `import a, { b, c as d }, * as e from "x"`. Side-effect imports bind nothing."""
    names = []

    for node in walk(statement):
        if node.type == "import_specifier":
            names.append((node.child_by_field_name("alias") or node.child_by_field_name("name")).text.decode())
        elif node.type in ("import_clause", "namespace_import"):
            names += [child.text.decode() for child in node.children if child.type == "identifier"]

    return names

def rust_bound_names(declaration):
    """Names from a `use` line: the last segment of each path, or its `as` alias. Wildcards bind nothing."""
    names = []

    for node in walk(declaration):
        parent = node.parent

        if node.type != "identifier" or parent is None or parent.type == "use_wildcard":
            continue

        if parent.type == "use_as_clause":
            names += [node.text.decode()] if node == parent.child_by_field_name("alias") else []
        elif parent.type == "scoped_identifier":
            is_path_of_longer = parent.parent.type in ("scoped_identifier", "scoped_use_list", "use_as_clause") and parent.parent.child_by_field_name("path") == parent

            names += [node.text.decode()] if node == parent.child_by_field_name("name") and not is_path_of_longer else []
        elif parent.type in ("use_list", "use_declaration"):
            names.append(node.text.decode())

    return names

def hare_bound_names(statement):
    """Names from a `use` line: `use a::b;` binds b, `use x = a::b;` binds x and `use a::{b, c};` binds b and c."""
    text = statement.text.decode().removeprefix("use").removesuffix(";").strip()

    if "=" in text:
        return [text.split("=")[0].strip()]

    if "{" in text:
        return re.findall(r"\w+", text[text.index("{"):])

    return [] if text.endswith("*") else [text.split("::")[-1].strip()]

def go_bound_names(spec):
    """The name a Go import is used by: its alias, or the last part of its path. `_` and `.` imports bind nothing to look for."""
    alias = spec.child_by_field_name("name")

    if alias is not None:
        return [] if alias.text in (b"_", b".") else [alias.text.decode()]

    parts = spec.child_by_field_name("path").text.decode().strip('"`').split("/")
    last = parts[-2] if re.fullmatch(r"v\d+", parts[-1]) and len(parts) > 1 else parts[-1]  # example.com/lib/v2 is used as lib

    return [re.sub(r"\.v\d+$|-go$", "", last)]  # gopkg.in/yaml.v3 is used as yaml

def tree_imports(root, lines, language):
    """(imported names, line numbers of the unused ones)."""
    used = counts_outside_imports(root)
    total, unused = 0, []

    for node in walk(root):
        line = node.start_point.row + 1

        if node.type not in IMPORT_TYPES or NOQA_MARKER in lines[line - 1]:
            continue

        if any(child.type == PUBLIC_MARKER for child in node.children):
            continue

        bound_names = {RUST: rust_bound_names, HARE: hare_bound_names, GO: go_bound_names}
        names = bound_names.get(language, typescript_bound_names)(node)
        total += len(names)
        unused += [line for name in names if used[name] <= 0]

    return total, unused
