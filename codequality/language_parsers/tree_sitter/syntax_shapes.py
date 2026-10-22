# Node type names from the tree-sitter grammars, so the code that walks trees can stay language-neutral.

# Field names the grammars give to the parts of a node.
NAME_FIELD, BODY_FIELD, OPERATOR_FIELD, LEFT_FIELD, FUNCTION_FIELD = "name", "body", "operator", "left", "function"
CALL_EXPRESSION = "call_expression"
FIRST_CHILD = "#first"  # stands in for a field name when the grammar gives the declared name no field (Hare)
WHOLE_NODE = "#whole"  # the node itself holds the names, like Fortran's argument list

FUNCTION_TYPES = {
    "rust": {"function_item"},
    "typescript": {"function_declaration", "generator_function_declaration", "method_definition",
                   "arrow_function", "function_expression"},
    "hare": {"function_declaration"},
    "c": {"function_definition"},
    "go": {"function_declaration", "method_declaration", "func_literal"},
    "mojo": {"function_definition"},
    "fortran": {"function", "subroutine", "program"},
    "csharp": {"method_declaration", "constructor_declaration", "local_function_statement"},  # lambdas are not counted as functions
    "rexx": {"routine_definition"},  # a label and everything up to the next label
}

# Declarations that create local variables: node type -> the field holding the new names.
BINDING_FIELDS = {
    "rust": {"let_declaration": "pattern", "parameter": "pattern", "for_expression": "pattern",
             "let_condition": "pattern", "match_arm": "pattern"},

    "typescript": {"variable_declarator": "name", "required_parameter": "pattern",
                   "optional_parameter": "pattern", "arrow_function": "parameter",
                   "for_in_statement": "left", "catch_clause": "parameter"},

    "hare": {"let_declaration": FIRST_CHILD, "parameter": FIRST_CHILD, "let_expression": FIRST_CHILD},
    "c": {"declaration": "declarator", "init_declarator": "declarator", "parameter_declaration": "declarator"},
    "go": {"short_var_declaration": "left", "var_spec": "name", "parameter_declaration": "name", "range_clause": "left"},
    "mojo": {"parameter": "name", "assignment": "left", "for_statement": "left", "for_in_clause": "left", "except_clause": FIRST_CHILD},
    "fortran": {"variable_declaration": "declarator", "parameters": WHOLE_NODE, "loop_control_expression": FIRST_CHILD},
    "csharp": {"variable_declarator": "name", "parameter": "name", "foreach_statement": "left", "catch_declaration": "name"},
    "rexx": {"parameter": "name", "assignment_statement": "left", "parse_statement": "target", "for_statement": "left"},
}

# Node types that are a variable name (field names and type names are different node types).
IDENTIFIER_TYPES = {
    "rust": {"identifier"},
    "typescript": {"identifier", "shorthand_property_identifier", "shorthand_property_identifier_pattern"},
    "hare": {"identifier"},
    "c": {"identifier"},
    "go": {"identifier"},
    "mojo": {"identifier"},
    "fortran": {"identifier"},
    "csharp": {"identifier"},
    "rexx": {"identifier"},
}

# Each of these adds one path through the function.
BRANCH_TYPES = {
    "rust": {"if_expression", "while_expression", "for_expression", "loop_expression", "match_arm"},
    "typescript": {"if_statement", "for_statement", "for_in_statement", "while_statement", "do_statement",
                   "switch_case", "catch_clause", "ternary_expression"},
    "hare": {"if_statement", "for_statement", "case"},
    "c": {"if_statement", "for_statement", "while_statement", "do_statement", "case_statement", "conditional_expression"},
    "go": {"if_statement", "for_statement", "expression_case", "default_case", "type_case", "communication_case"},
    "mojo": {"if_statement", "elif_clause", "for_statement", "while_statement", "except_clause", "case_clause", "boolean_operator",
             "conditional_expression"},
    "fortran": {"if_statement", "elseif_clause", "do_loop", "case_statement", "where_statement"},
    "csharp": {"if_statement", "for_statement", "foreach_statement", "while_statement", "do_statement", "switch_section", "catch_clause",
               "conditional_expression", "switch_expression_arm"},
    "rexx": {"if_statement", "for_statement", "when_clause", "otherwise_clause", "boolean_operator"},  # `&` and `|` join conditions
}

BRANCH_OPERATORS = {"&&", "||", "??"}

# Fortran does not care about case: `Total` and `total` are the same variable.
CASE_INSENSITIVE_LANGUAGES = {"fortran", "rexx"}
