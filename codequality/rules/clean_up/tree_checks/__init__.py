from collections import Counter

from ..deor_checks.deor_cleanup import deor_cleanup
from ....source_code import DEOR
from ....language_parsers.tree_sitter.parse_tree import parse_tree
from ..Cleanup_Findings import Cleanup_Findings, Name_Usage
from .imports import tree_imports
from .name_usage import tree_name_usage
from .unreachable import tree_unreachable
from .variables import tree_variables

def analyze_deor(source):
    """Deor imports are global and nothing in it is private, so only variables and unreachable code can be left over."""
    variables_total, unused_variables, statements_total, unreachable = deor_cleanup(source)

    return Cleanup_Findings(0, [], variables_total, unused_variables, statements_total, unreachable), Name_Usage([], Counter())

def analyze_tree(source, language):
    """(Cleanup_Findings, Name_Usage) for one Rust, TypeScript or Deor file."""

    if language == DEOR:
        return analyze_deor(source)

    root = parse_tree(source, language)
    imports_total, unused_imports = tree_imports(root, source.splitlines(), language)
    variables_total, unused_variables = tree_variables(root, language)
    statements_total, unreachable = tree_unreachable(root)

    findings = Cleanup_Findings(imports_total, sorted(unused_imports), variables_total, sorted(unused_variables),
                                statements_total, sorted(unreachable))

    return findings, tree_name_usage(root, language)
