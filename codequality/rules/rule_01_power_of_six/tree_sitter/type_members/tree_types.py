from .....language_parsers.tree_sitter.parse_tree import parse_tree
from .....language_parsers.tree_sitter.tree_walk import walk
from .....source_code import TYPESCRIPT
from .lookups.type_names import named
from .Type_Info import Type_Info
from .type_rules import ANY_MEMBER, FIELD, METHOD, TYPE_RULES

SKIPPED = {"visibility_modifier", "attribute_item", "line_comment", "block_comment", "comment", "ERROR"}
ANONYMOUS = "(anonymous)"

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

def type_info_for(node, rule):
    """The Type_Info for one syntax node, or None when it is not a declaration worth counting."""
    name = rule.name(node)

    if name is None and rule.owner:
        return None

    body = rule.body(node)

    if body is None and not rule.owner and not record_parameters(node):  # a bodiless `struct S x;` is a use, not a declaration
        return None

    counts = count_members(body, rule)

    return Type_Info(name.text.decode() if name is not None else ANONYMOUS, node.start_point.row + 1,
                     counts[FIELD] + record_parameters(node), counts[METHOD] + rule.base_methods)

def tree_types(source, language):
    """A Type_Info for every struct, class, enum, interface and component (with its methods) in a tree-sitter language."""
    tree = parse_tree(source, language)
    infos, owners = [], []

    for node in walk(tree):
        rule = TYPE_RULES[language].get(node.type)
        info = type_info_for(node, rule) if rule else None

        if info:
            (owners if rule.owner else infos).append(info)

    if language == TYPESCRIPT:
        infos += component_infos(tree)

    return merge_owners(infos, owners)
