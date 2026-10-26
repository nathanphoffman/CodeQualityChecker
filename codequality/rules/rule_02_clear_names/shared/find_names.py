import re

from ..deor.deor_names import deor_kinded_names
from ..python.python_names import python_kinded_names
from .name_styles import CONSTANT, FUNCTION, TYPE, VALUE, VARIABLE, VARIANT
from ....source_code import DEOR, NAME_GROUP, PYTHON, SUFFIX_LANGUAGE, blank_out_text, read_source
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.syntax_shapes import FIRST_CHILD, NAME_FIELD
from ....language_parsers.tree_sitter.tree_walk import bound_nodes, declarator_name, identifiers_in, walk

# Clever on purpose: each pattern captures a declared name, one per kind of declaration.
# `let` skips destructuring like `let Some(x)` or `let Point { x }` by refusing a name followed by "(" or "{".
NAME_PATTERNS = {
    "rust": [
        (FUNCTION, re.compile(r"\bfn\s+(?P<name>\w+)")),  # "fn" then the name
        (VARIABLE, re.compile(r"\blet\s+(?:mut\s+)?(?P<name>\w+)\b(?!\s*[({])")),  # "let", optional "mut", then the name

        (CONSTANT, re.compile(r"\b(?:const|static)\s+(?:mut\s+)?(?P<name>\w+)\s*:")),  # "const" or "static", optional "mut", a name, then ":"
        (TYPE, re.compile(r"\b(?:struct|enum|trait|type|union)\s+(?P<name>\w+)")),  # a type keyword then the name
        (VARIABLE, re.compile(r"\bmod\s+(?P<name>\w+)")),  # a module is named like a variable, not a type
        (VARIABLE, re.compile(r"\bfor\s+(?P<name>\w+)\s+in\b")),  # "for", the loop variable, then "in"
    ],
    "hare": [
        (FUNCTION, re.compile(r"\bfn\s+(?P<name>\w+)")),  # "fn" then the name
        (VARIABLE, re.compile(r"\blet\s+(?P<name>\w+)\b")),  # "let" then the name; `let (a, b)` is skipped because "(" follows
        (CONSTANT, re.compile(r"\bdef\s+(?P<name>\w+)\b")),  # "def" then the name

        (VARIABLE, re.compile(r"\bconst\s+(?P<name>\w+)\s*[:=]")),  # "const", a name, then ":" or "=" (so `const str` in a type is not a name)
        (TYPE, re.compile(r"\btype\s+(?P<name>\w+)")),  # "type" then the name
    ],
    "typescript": [
        (FUNCTION, re.compile(r"\bfunction\s*\*?\s*(?P<name>\w+)")),  # "function", optional "*", then the name

        (VALUE, re.compile(r"\bconst\s+(?P<name>\w+)")),  # "const" then the name
        (VARIABLE, re.compile(r"\b(?:let|var)\s+(?P<name>\w+)")),  # "let" or "var" then the name
        (TYPE, re.compile(r"\b(?:class|interface|type|enum)\s+(?P<name>\w+)")),  # a type keyword then the name
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

# C, Go, Mojo and Fortran are read entirely from the syntax tree: node type -> (the field holding the names it declares, what kind of name that is).
# Go lists several names in one field (`a, b := ...`), C and Fortran declarators wrap the name (`*name`, `name(10)`).
DECLARATION_FIELDS = {
    "c": {"function_definition": ("declarator", FUNCTION), "declaration": ("declarator", VARIABLE), "init_declarator": ("declarator", VARIABLE),
          "parameter_declaration": ("declarator", VARIABLE), "field_declaration": ("declarator", VARIABLE), "type_definition": ("declarator", TYPE),
          "enumerator": (NAME_FIELD, CONSTANT), "struct_specifier": (NAME_FIELD, TYPE), "enum_specifier": (NAME_FIELD, TYPE),
          "union_specifier": (NAME_FIELD, TYPE), "preproc_def": (NAME_FIELD, CONSTANT), "preproc_function_def": (NAME_FIELD, CONSTANT)},
    "go": {"function_declaration": (NAME_FIELD, FUNCTION), "method_declaration": (NAME_FIELD, FUNCTION), "var_spec": (NAME_FIELD, VARIABLE),
           "const_spec": (NAME_FIELD, CONSTANT), "type_spec": (NAME_FIELD, TYPE), "parameter_declaration": (NAME_FIELD, VARIABLE),
           "field_declaration": (NAME_FIELD, VARIABLE), "short_var_declaration": ("left", VARIABLE), "range_clause": ("left", VARIABLE)},
    "mojo": {"function_definition": (NAME_FIELD, FUNCTION), "struct_definition": (NAME_FIELD, TYPE), "trait_definition": (NAME_FIELD, TYPE),
             "parameter": (NAME_FIELD, VARIABLE), "assignment": ("left", VALUE), "for_statement": ("left", VARIABLE),
             "for_in_clause": ("left", VARIABLE), "aliased_import": ("alias", VARIABLE)},
    "fortran": {"function_statement": (NAME_FIELD, FUNCTION), "subroutine_statement": (NAME_FIELD, FUNCTION),
                "variable_declaration": ("declarator", VARIABLE)},
    "csharp": {"method_declaration": (NAME_FIELD, FUNCTION), "constructor_declaration": (NAME_FIELD, FUNCTION),
               "local_function_statement": (NAME_FIELD, FUNCTION), "class_declaration": (NAME_FIELD, TYPE), "struct_declaration": (NAME_FIELD, TYPE),
               "interface_declaration": (NAME_FIELD, TYPE), "enum_declaration": (NAME_FIELD, TYPE), "record_declaration": (NAME_FIELD, TYPE),
               "enum_member_declaration": (NAME_FIELD, CONSTANT), "property_declaration": (NAME_FIELD, VALUE), "parameter": (NAME_FIELD, VARIABLE),
               "variable_declarator": (NAME_FIELD, VARIABLE), "foreach_statement": ("left", VARIABLE), "catch_declaration": (NAME_FIELD, VARIABLE)},
    "rexx": {"routine_definition": (NAME_FIELD, FUNCTION), "parameter": (NAME_FIELD, VARIABLE), "assignment_statement": ("left", VARIABLE),
             "parse_statement": ("target", VARIABLE), "for_statement": ("left", VARIABLE)},
}

def named_part(node):
    return [node.child_by_field_name(NAME_FIELD)]

def typescript_enum_members(node):
    return [child for child in node.named_children if child.type == "property_identifier"]  # members with no `= value`

def first_identifier(node):
    return node.named_children[:1]

# Enum members and struct fields, which the patterns and declaration fields above don't reach: node type -> (how to find the name nodes in it, what kind they are).
MEMBER_NODES = {
    "rust": {"enum_variant": (named_part, VARIANT), "field_declaration": (named_part, VARIABLE)},
    "typescript": {"enum_assignment": (named_part, VARIANT), "enum_body": (typescript_enum_members, VARIANT),  # `Green = 2` is an assignment, `Red` is a bare name
                   "property_signature": (named_part, VARIABLE), "public_field_definition": (named_part, VARIABLE)},
    "hare": {"enum_field": (first_identifier, VARIANT), "field": (first_identifier, VARIABLE)},
}

def member_names(source, language):
    """(name, kind) for every enum member and struct field in a language that MEMBER_NODES knows."""
    found = []

    for node in walk(parse_tree(source, language)):
        finder, kind = MEMBER_NODES[language].get(node.type, (None, None))

        found += [(part.text.decode(), kind) for part in finder(node)] if finder else []

    return found

def declared_in(node):
    if node.type in ("expression_list", "pattern"):
        return [part.text.decode() for part in node.named_children if part.type == "identifier"]

    found = declarator_name(node)

    return [found.text.decode()] if found else []

def declared_names(source, language):
    """(name, kind) for every name a tree-sitter language declares."""
    names = []

    for node in walk(parse_tree(source, language)):
        field, kind = DECLARATION_FIELDS[language].get(node.type, (None, None))

        for declared in node.children_by_field_name(field) if field else []:
            names += [(name, kind) for name in declared_in(declared)]

    return names

def find_kinded_names(source, language):
    """(name, kind) for every name the source declares, where kind is function, type, constant, variable or value."""
    # Python isn't in NAME_PATTERNS: its parser finds names exactly, so no patterns are needed.
    if language == PYTHON:
        found = python_kinded_names(source)
    elif language == DEOR:
        found = deor_kinded_names(source)
    elif language in DECLARATION_FIELDS:
        found = declared_names(source, language)
    else:
        text = blank_out_text(source, language)
        # one (name, kind) per match of every pattern, so each kind of declaration is found by its own pattern
        found = [(match.group(NAME_GROUP), kind) for kind, pattern in NAME_PATTERNS[language] for match in pattern.finditer(text)]
        found += [(name, VARIABLE) for name in parameter_names(source, language)]
        found += member_names(source, language)

    return [(name, kind) for name, kind in found if name != "_"]

def find_names(source, language):
    return [name for name, _ in find_kinded_names(source, language)]

def kinded_names_by_file(project):
    """{path: (language, [(name, kind), ...])} for every source file in the project."""

    def read_all():
        return {path: (SUFFIX_LANGUAGE[path.suffix], find_kinded_names(read_source(path), SUFFIX_LANGUAGE[path.suffix]))
                for path in project.files(*SUFFIX_LANGUAGE)}

    return project.remember("kinded_names_by_file", read_all)

def kinded_names_by_language(project):
    """{language: [(name, kind), ...]} for every source file in the project."""
    found = {}

    for language, kinded in kinded_names_by_file(project).values():
        found.setdefault(language, []).extend(kinded)

    return found

def names_in_project(project):
    # flattens the per-language lists into one list of names
    return [name for kinded in kinded_names_by_language(project).values() for name, _ in kinded]
