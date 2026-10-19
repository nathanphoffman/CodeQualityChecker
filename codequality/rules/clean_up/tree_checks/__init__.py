from ....tree_sitter_support.parse_tree import parse_tree
from ..Cleanup_Findings import Cleanup_Findings
from .imports import tree_imports
from .name_usage import tree_name_usage
from .unreachable import tree_unreachable
from .variables import tree_variables

def analyze_tree(source, language):
    """(Cleanup_Findings, Name_Usage) for one Rust or TypeScript file."""
    root = parse_tree(source, language)
    imports_total, unused_imports = tree_imports(root, source.splitlines(), language)
    variables_total, unused_variables = tree_variables(root, language)
    statements_total, unreachable = tree_unreachable(root)

    findings = Cleanup_Findings(imports_total, sorted(unused_imports), variables_total, sorted(unused_variables),
                                statements_total, sorted(unreachable))

    return findings, tree_name_usage(root, language)
