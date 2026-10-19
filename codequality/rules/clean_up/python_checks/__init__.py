from ....python_support.parse_python import parse_python
from ..Cleanup_Findings import Cleanup_Findings
from .imports import python_imports
from .name_usage import python_name_usage
from .unreachable import python_unreachable
from .variables import python_variables

def analyze_python(source, is_package_init):
    """(Cleanup_Findings, Name_Usage) for one Python file."""
    tree = parse_python(source)
    imports_total, unused_imports = python_imports(tree, source.splitlines(), is_package_init)
    variables_total, unused_variables = python_variables(tree)
    statements_total, unreachable = python_unreachable(tree)

    findings = Cleanup_Findings(imports_total, sorted(unused_imports), variables_total, sorted(unused_variables),
                                statements_total, sorted(unreachable))

    return findings, python_name_usage(tree)
