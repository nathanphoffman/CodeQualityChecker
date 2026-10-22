import ast

from ...language_parsers.python.parse_python import parse_python
from ...language_parsers.deor.declarations import declarations_in
from ...language_parsers.deor.tree import parse_deor
from ...source_code import C_LANG, CSHARP, DEOR, FORTRAN, GO, HARE, MOJO, PYTHON, REXX, RUST, SUFFIX_LANGUAGE, TYPESCRIPT, read_source
from ...language_parsers.tree_sitter.parse_tree import parse_tree
from ...language_parsers.tree_sitter.syntax_shapes import FUNCTION_TYPES
from ...language_parsers.tree_sitter.tree_functions import function_name
from ...language_parsers.tree_sitter.tree_walk import squashed, walk
from ..rule_05_be_secure.shared.uses import find_uses

TYPESCRIPT_TEST_CALLS = {"it", "test", "it.only", "test.only"}
CALLBACK_MARKERS = ("=>", "function")  # a real test passes its body as a function: test("name", () => ...)
PYTHON_TEST_PREFIX = "test"
DEOR_EXPECTATION = "expect"  # a comment starting "expect:" or "expect-error:" in a Deor test example
RUST_TEST_ATTRIBUTE_END = "test]"  # #[test] and #[tokio::test], but not #[cfg(test)]
HARE_TEST_ATTRIBUTE = "@test"
GO_TEST_PREFIX = "Test"  # func TestAdd(t *testing.T)
CSHARP_TEST_ATTRIBUTES = {"Fact", "Theory", "Test", "TestCase", "TestMethod", "DataTestMethod"}  # xUnit, NUnit and MSTest

def count_python_tests(source):
    functions = [node for node in ast.walk(parse_python(source)) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]

    return len([function for function in functions if function.name.startswith(PYTHON_TEST_PREFIX)])

def has_test_attribute(function):
    """Whether the attributes stacked above a Rust function include #[test] or #[something::test]."""
    sibling = function.prev_named_sibling

    while sibling is not None and sibling.type in ("attribute_item", "line_comment", "block_comment"):
        if sibling.type == "attribute_item" and squashed(sibling.text.decode()).endswith(RUST_TEST_ATTRIBUTE_END):
            return True

        sibling = sibling.prev_named_sibling

    return False

def count_rust_tests(source):
    return len([node for node in walk(parse_tree(source, RUST)) if node.type == "function_item" and has_test_attribute(node)])

def count_hare_tests(source):
    functions = [node for node in walk(parse_tree(source, HARE)) if node.type == "function_declaration"]

    return len([function for function in functions if any(child.text == HARE_TEST_ATTRIBUTE.encode() for child in function.children
                                                           if child.type == "function_attribute")])

def count_named_tests(source, language, prefix):
    """Functions whose name starts with this prefix: C has no test attribute, so `test_` is the usual habit, and Go's tools look for `Test`."""
    functions = [node for node in walk(parse_tree(source, language)) if node.type in FUNCTION_TYPES[language]]

    return len([function for function in functions if function_name(function).startswith(prefix)])  # Fortran names are lower-cased

def count_c_tests(source):
    return count_named_tests(source, C_LANG, PYTHON_TEST_PREFIX)

def count_csharp_tests(source):
    """Methods carrying a test attribute like [Fact] or [TestMethod]. `Attribute` on the end of a name is optional in C#."""
    attributes = [node for node in walk(parse_tree(source, CSHARP)) if node.type == "attribute" and node.parent.parent.type == "method_declaration"]
    names = [attribute.child_by_field_name("name").text.decode().split(".")[-1].removesuffix("Attribute") for attribute in attributes]

    return len([name for name in names if name in CSHARP_TEST_ATTRIBUTES])

def count_mojo_tests(source):
    return count_named_tests(source, MOJO, PYTHON_TEST_PREFIX)

def count_fortran_tests(source):
    return count_named_tests(source, FORTRAN, PYTHON_TEST_PREFIX)

def count_rexx_tests(source):
    return count_named_tests(source, REXX, PYTHON_TEST_PREFIX)

def count_go_tests(source):
    return count_named_tests(source, GO, GO_TEST_PREFIX)

def count_typescript_tests(source):
    calls = [use for use in find_uses(source, TYPESCRIPT) if use.name in TYPESCRIPT_TEST_CALLS]

    # counts the calls whose text contains any of the callback markers
    return len([call for call in calls if any(marker in call.text for marker in CALLBACK_MARKERS)])

def count_deor_tests(source):
    """Functions named test..., plus one for a file that states what it expects (# expect:, # expect-error: ...), which is how
    the Deor test runner reads a test example."""

    parsed = parse_deor(source)
    functions = [item for item in declarations_in(parsed.roots, ("fn",)) if item.name.startswith(PYTHON_TEST_PREFIX)]
    states_expectation = any(line.comment is not None and line.comment.strip().startswith(DEOR_EXPECTATION) for line in parsed.lines)

    return len(functions) + states_expectation

def count_tests_in_project(project):
    """Tests in every source file, test folders included."""
    counters = {PYTHON: count_python_tests, RUST: count_rust_tests, TYPESCRIPT: count_typescript_tests, DEOR: count_deor_tests,
                HARE: count_hare_tests, C_LANG: count_c_tests, GO: count_go_tests,
                MOJO: count_mojo_tests, FORTRAN: count_fortran_tests, CSHARP: count_csharp_tests, REXX: count_rexx_tests}
    total = 0

    for path in project.files(*SUFFIX_LANGUAGE):
        total += counters[SUFFIX_LANGUAGE[path.suffix]](read_source(path))

    return total
