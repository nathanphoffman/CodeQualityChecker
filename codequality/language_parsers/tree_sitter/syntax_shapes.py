# Node type names from the tree-sitter grammars, so the code that walks trees can stay language-neutral.

# Field names the grammars give to the parts of a node.
NAME_FIELD, BODY_FIELD, OPERATOR_FIELD = "name", "body", "operator"

FUNCTION_TYPES = {
    "rust": {"function_item"},
    "typescript": {"function_declaration", "generator_function_declaration", "method_definition",
                   "arrow_function", "function_expression"},
}

# Declarations that create local variables: node type -> the field holding the new names.
BINDING_FIELDS = {
    "rust": {"let_declaration": "pattern", "parameter": "pattern", "for_expression": "pattern",
             "let_condition": "pattern", "match_arm": "pattern"},

    "typescript": {"variable_declarator": "name", "required_parameter": "pattern",
                   "optional_parameter": "pattern", "arrow_function": "parameter",
                   "for_in_statement": "left", "catch_clause": "parameter"},
}

# Node types that are a variable name (field names and type names are different node types).
IDENTIFIER_TYPES = {
    "rust": {"identifier"},
    "typescript": {"identifier", "shorthand_property_identifier", "shorthand_property_identifier_pattern"},
}

# Each of these adds one path through the function.
BRANCH_TYPES = {
    "rust": {"if_expression", "while_expression", "for_expression", "loop_expression", "match_arm"},
    "typescript": {"if_statement", "for_statement", "for_in_statement", "while_statement", "do_statement",
                   "switch_case", "catch_clause", "ternary_expression"},
}

BRANCH_OPERATORS = {"&&", "||", "??"}
