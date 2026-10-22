import re

from ..deor.deor_names import deor_names
from ..python.python_names import python_names
from ....source_code import DEOR, NAME_GROUP, PYTHON, SUFFIX_LANGUAGE, blank_out_text, read_source
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.syntax_shapes import FIRST_CHILD
from ....language_parsers.tree_sitter.tree_walk import bound_nodes, declarator_name, identifiers_in, walk

# Clever on purpose: each pattern captures a declared name, one per kind of declaration.
# `let` skips destructuring like `let Some(x)` or `let Point { x }` by refusing a name followed by "(" or "{".
NAME_PATTERNS = {
    "rust": [
        re.compile(r"\bfn\s+(?P<name>\w+)"),  # "fn" then the name
        re.compile(r"\blet\s+(?:mut\s+)?(?P<name>\w+)\b(?!\s*[({])"),  # "let", optional "mut", then the name

        re.compile(r"\b(?:const|static)\s+(?:mut\s+)?(?P<name>\w+)\s*:"),  # "const" or "static", optional "mut", a name, then ":"
        re.compile(r"\b(?:struct|enum|trait|type|union|mod)\s+(?P<name>\w+)"),  # a type keyword then the name
        re.compile(r"\bfor\s+(?P<name>\w+)\s+in\b"),  # "for", the loop variable, then "in"
    ],
    "hare": [
        re.compile(r"\bfn\s+(?P<name>\w+)"),  # "fn" then the name
        re.compile(r"\b(?:let|def)\s+(?P<name>\w+)\b"),  # "let" or "def" then the name; `let (a, b)` is skipped because "(" follows

        re.compile(r"\bconst\s+(?P<name>\w+)\s*[:=]"),  # "const", a name, then ":" or "=" (so `const str` in a type is not a name)
        re.compile(r"\btype\s+(?P<name>\w+)"),  # "type" then the name
    ],
    "typescript": [
        re.compile(r"\bfunction\s*\*?\s*(?P<name>\w+)"),  # "function", optional "*", then the name

        re.compile(r"\b(?:const|let|var)\s+(?P<name>\w+)"),  # a variable keyword then the name
        re.compile(r"\b(?:class|interface|type|enum)\s+(?P<name>\w+)"),  # a type keyword then the name
    ],
}

# Parameters can't be found by a pattern (types, defaults and destructuring get in the way), so the syntax tree finds them:
# node type -> the field holding the new names. Rust closures list bare names between pipes, so the whole node is read.
PARAMETER_FIELDS = {
    "rust": {"parameter": "pattern", "closure_parameters": None},
    "hare": {"parameter": FIRST_CHILD},
    "typescript": {"required_parameter": "pattern", "optional_parameter": "pattern", "arrow_function": "parameter"},
}

def parameter_names(source, language):
    names = []

    for node in walk(parse_tree(source, language)):
        if node.type not in PARAMETER_FIELDS[language]:
            continue

        field = PARAMETER_FIELDS[language][node.type]

        for declared in bound_nodes(node, field) if field else [node]:
            names += identifiers_in(declared, language)

    return names

# C, Go, Mojo and Fortran are read entirely from the syntax tree: node type -> the field holding the names it declares.
# Go lists several names in one field (`a, b := ...`), C and Fortran declarators wrap the name (`*name`, `name(10)`).
DECLARATION_FIELDS = {
    "c": {"function_definition": "declarator", "declaration": "declarator", "init_declarator": "declarator",
          "parameter_declaration": "declarator", "field_declaration": "declarator", "type_definition": "declarator",
          "enumerator": "name", "struct_specifier": "name", "enum_specifier": "name", "union_specifier": "name",
          "preproc_def": "name", "preproc_function_def": "name"},
    "go": {"function_declaration": "name", "method_declaration": "name", "var_spec": "name", "const_spec": "name",
           "type_spec": "name", "parameter_declaration": "name", "field_declaration": "name", "short_var_declaration": "left",
           "range_clause": "left"},
    "mojo": {"function_definition": "name", "struct_definition": "name", "trait_definition": "name", "parameter": "name",
             "assignment": "left", "for_statement": "left", "for_in_clause": "left", "aliased_import": "alias"},
    "fortran": {"function_statement": "name", "subroutine_statement": "name", "variable_declaration": "declarator"},
    "csharp": {"method_declaration": "name", "constructor_declaration": "name", "local_function_statement": "name",
               "class_declaration": "name", "struct_declaration": "name", "interface_declaration": "name", "enum_declaration": "name",
               "record_declaration": "name", "enum_member_declaration": "name", "property_declaration": "name", "parameter": "name",
               "variable_declarator": "name", "foreach_statement": "left", "catch_declaration": "name"},
}

def declared_in(node):
    if node.type in ("expression_list", "pattern"):
        return [part.text.decode() for part in node.named_children if part.type == "identifier"]

    found = declarator_name(node)

    return [found.text.decode()] if found else []

def declared_names(source, language):
    names = []

    for node in walk(parse_tree(source, language)):
        field = DECLARATION_FIELDS[language].get(node.type)

        for declared in node.children_by_field_name(field) if field else []:
            names += declared_in(declared)

    return names

def find_names(source, language):
    # Python isn't in NAME_PATTERNS: its parser finds names exactly, so no patterns are needed.
    if language == PYTHON:
        return python_names(source)

    if language == DEOR:
        return deor_names(source)

    if language in DECLARATION_FIELDS:
        return [name for name in declared_names(source, language) if name != "_"]

    text = blank_out_text(source, language)
    names = []

    for pattern in NAME_PATTERNS[language]:
        names += [match.group(NAME_GROUP) for match in pattern.finditer(text)]

    names += parameter_names(source, language)

    return [name for name in names if name != "_"]

def names_in_project(project):
    names = []

    for path in project.files(*SUFFIX_LANGUAGE):
        names += find_names(read_source(path), SUFFIX_LANGUAGE[path.suffix])

    return names
