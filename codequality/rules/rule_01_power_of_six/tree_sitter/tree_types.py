from typing import Callable, NamedTuple

from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ....language_parsers.tree_sitter.syntax_shapes import NAME_FIELD
from ....language_parsers.tree_sitter.tree_walk import walk
from ..shared.Type_Info import Type_Info

FIELD, METHOD = "fields", "methods"
ANY_MEMBER = "*"  # in a members table: every member not listed
SKIPPED = {"visibility_modifier", "attribute_item", "line_comment", "block_comment", "comment", "ERROR"}
CONSTRUCTORS = {"constructor", "__init__"}  # a constructor is not counted as one of the type's methods
ANONYMOUS = "(anonymous)"

def one(node):
    return 1

def named(node):
    return node.child_by_field_name(NAME_FIELD)

def declarators(node):
    """`int a, b;` declares two members in one node."""

    return max(1, len(node.children_by_field_name("declarator")))

def names_listed(node):
    """Go's `x, y int` declares two fields in one node."""

    return max(1, len(node.children_by_field_name(NAME_FIELD)))

def variable_declarators(node):
    return max(1, sum(part.type == "variable_declarator" for part in walk(node)))

def unless_constructor(node):
    name = named(node)

    return 0 if name is not None and name.text.decode() in CONSTRUCTORS else 1

def procedures(node):
    return sum(child.type == "procedure_statement" for child in node.named_children)

class Type_Rule(NamedTuple):
    name: Callable  # node -> the node holding the type's name, or None
    body: Callable  # node -> the node whose children are the members, or None when there are none to count
    members: dict  # child node type -> (FIELD or METHOD, how many members that child is)
    owner: bool = False  # an impl block or a Go method: it adds members to a type declared elsewhere, so it merges by name
    base_methods: int = 0  # members the node is by itself: a Go method declaration is one method

def body_field(node):
    return node.child_by_field_name("body")

def whole_node(node):
    return node

def own_type_name(node):
    return node.child_by_field_name("type")

def type_declaration_name(node):
    """Hare names a struct or enum on the `type name = ...` declaration around it."""
    ancestor = node.parent

    while ancestor is not None and ancestor.type != "type_declaration":
        ancestor = ancestor.parent

    return ancestor.named_children[0] if ancestor is not None else None

def fortran_type_name(node):
    return next((part.named_children[0] for part in node.named_children if part.type == "derived_type_statement"), None)

def go_body(node):
    kind = node.child_by_field_name("type")

    if kind is not None and kind.type == "struct_type":
        return kind.named_children[0] if kind.named_children else None

    return kind if kind is not None and kind.type == "interface_type" else None

def go_receiver_name(node):
    receiver = node.child_by_field_name("receiver")

    return next((part for part in walk(receiver) if part.type == "type_identifier"), None) if receiver is not None else None

def nothing(node):
    return None

def object_type_body(node):
    value = node.child_by_field_name("value")

    return value if value is not None and value.type == "object_type" else None

CLASS_MEMBERS = {"public_field_definition": (FIELD, one), "method_definition": (METHOD, unless_constructor), "abstract_method_signature": (METHOD, one)}
SHAPE_MEMBERS = {"property_signature": (FIELD, one), "method_signature": (METHOD, one)}
C_MEMBERS = {"field_declaration": (FIELD, declarators)}
CSHARP_MEMBERS = {"field_declaration": (FIELD, variable_declarators), "property_declaration": (FIELD, one), "method_declaration": (METHOD, one)}
CSHARP_TYPES = ("class_declaration", "struct_declaration", "interface_declaration", "record_declaration", "record_struct_declaration")
MOJO_MEMBERS = {"assignment": (FIELD, one), "function_definition": (METHOD, unless_constructor)}

# node type -> Type_Rule, for each language read from the syntax tree. Python and Deor have their own readers, and Rexx has no types.
TYPE_RULES = {
    "rust": {
        "struct_item": Type_Rule(named, body_field, {ANY_MEMBER: (FIELD, one)}),  # named fields, or the types of a tuple struct
        "enum_item": Type_Rule(named, body_field, {"enum_variant": (FIELD, one)}),
        "trait_item": Type_Rule(named, body_field, {"function_item": (METHOD, one), "function_signature_item": (METHOD, one)}),
        "impl_item": Type_Rule(own_type_name, body_field, {"function_item": (METHOD, one)}, owner=True),
    },
    "typescript": {
        "class_declaration": Type_Rule(named, body_field, CLASS_MEMBERS),
        "abstract_class_declaration": Type_Rule(named, body_field, CLASS_MEMBERS),
        "interface_declaration": Type_Rule(named, body_field, SHAPE_MEMBERS),
        "enum_declaration": Type_Rule(named, body_field, {ANY_MEMBER: (FIELD, one)}),
        "type_alias_declaration": Type_Rule(named, object_type_body, SHAPE_MEMBERS),
    },
    "go": {
        "type_spec": Type_Rule(named, go_body, {"field_declaration": (FIELD, names_listed), "method_elem": (METHOD, one)}),
        "method_declaration": Type_Rule(go_receiver_name, nothing, {}, owner=True, base_methods=1),
    },
    "c": {
        "struct_specifier": Type_Rule(named, body_field, C_MEMBERS),
        "union_specifier": Type_Rule(named, body_field, C_MEMBERS),
        "enum_specifier": Type_Rule(named, body_field, {"enumerator": (FIELD, one)}),
    },
    "csharp": {**{kind: Type_Rule(named, body_field, CSHARP_MEMBERS) for kind in CSHARP_TYPES},
               "enum_declaration": Type_Rule(named, body_field, {"enum_member_declaration": (FIELD, one)})},
    "mojo": {
        "struct_definition": Type_Rule(named, body_field, MOJO_MEMBERS),
        "trait_definition": Type_Rule(named, body_field, MOJO_MEMBERS),
    },
    "hare": {
        "struct_type": Type_Rule(type_declaration_name, whole_node, {"field": (FIELD, one)}),
        "enum_type": Type_Rule(type_declaration_name, whole_node, {"enum_field": (FIELD, one)}),
    },
    "fortran": {
        "derived_type_definition": Type_Rule(fortran_type_name, whole_node, {"variable_declaration": (FIELD, declarators), "derived_type_procedures": (METHOD, procedures)}),
    },
    "rexx": {},
}

def count_members(body, rule):
    counts = {FIELD: 0, METHOD: 0}

    for child in body.named_children if body is not None else []:
        if child.type in SKIPPED:
            continue

        kind, how_many = rule.members.get(child.type) or rule.members.get(ANY_MEMBER) or (None, None)

        if kind:
            counts[kind] += how_many(child)

    return counts

def record_parameters(node):
    """A C# record `record R(int A, int B)` has a field for each parameter."""
    parameters = next((child for child in node.children if child.type == "parameter_list"), None) if node.type.startswith("record") else None

    return len(parameters.named_children) if parameters is not None else 0

def props_of_component(node):
    """The props a TypeScript component destructures: `function Card({ title, body })` or `const Card = ({ title, body }) => ...`. None for anything else."""
    function = node.child_by_field_name("value") if node.type == "variable_declarator" else node
    parameters = function.child_by_field_name("parameters") if function is not None else None
    first = parameters.named_children[0] if parameters is not None and parameters.named_children else None
    destructured = first.child_by_field_name("pattern") if first is not None else None

    return len(destructured.named_children) if destructured is not None and destructured.type == "object_pattern" else None

def component_infos(tree):
    """A Type_Info for every capitalized TypeScript function or arrow function that takes destructured props."""
    infos = []

    for node in walk(tree):
        if node.type not in ("function_declaration", "variable_declarator"):
            continue

        name = named(node)
        props = props_of_component(node)

        if props is not None and name is not None and name.text.decode()[:1].isupper():
            infos.append(Type_Info(name.text.decode(), node.start_point.row + 1, props, 0))

    return infos

def merge_owners(infos, owners):
    """Adds each owner's methods (impl blocks, Go methods) to the type of the same name in the file, or lists them alone when it is declared elsewhere."""
    by_name = {info.name: info for info in infos}

    for owner in owners:
        if owner.name in by_name:
            by_name[owner.name].methods += owner.methods
        else:
            by_name[owner.name] = owner

    return list(by_name.values()) if owners else infos

def tree_types(source, language):
    """A Type_Info for every struct, class, enum, interface and component (with its methods) in a tree-sitter language."""
    tree = parse_tree(source, language)
    infos, owners = [], []

    for node in walk(tree):
        rule = TYPE_RULES[language].get(node.type)
        name = rule.name(node) if rule else None

        if rule is None or (name is None and rule.owner):
            continue

        body = rule.body(node)

        if body is None and not rule.owner and not record_parameters(node):  # a bodiless `struct S x;` is a use, not a declaration
            continue

        counts = count_members(body, rule)
        info = Type_Info(name.text.decode() if name is not None else ANONYMOUS, node.start_point.row + 1,
                         counts[FIELD] + record_parameters(node), counts[METHOD] + rule.base_methods)
        (owners if rule.owner else infos).append(info)

    if language == "typescript":
        infos += component_infos(tree)

    return merge_owners(infos, owners)
