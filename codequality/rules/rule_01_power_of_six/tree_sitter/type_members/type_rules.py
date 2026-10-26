from typing import Callable, NamedTuple

from .lookups.member_counters import declarators, names_listed, one, procedures, unless_constructor, variable_declarators
from .lookups.type_bodies import body_field, go_body, nothing, object_type_body, whole_node
from .lookups.type_names import fortran_type_name, go_receiver_name, named, own_type_name, type_declaration_name

FIELD, METHOD = "fields", "methods"
ANY_MEMBER = "*"  # in a members table: every member not listed

class Type_Rule(NamedTuple):
    name: Callable  # node -> the node holding the type's name, or None
    body: Callable  # node -> the node whose children are the members, or None when there are none to count
    members: dict  # child node type -> (FIELD or METHOD, how many members that child is)
    owner: bool = False  # an impl block or a Go method: it adds members to a type declared elsewhere, so it merges by name
    base_methods: int = 0  # members the node is by itself: a Go method declaration is one method

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
