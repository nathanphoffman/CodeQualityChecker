import ast

from ...python_support.parse_python import parse_python
from ...source_code import PYTHON, RUST, SUFFIX_LANGUAGE, TYPESCRIPT, read_source
from ...tree_sitter_support.parse_tree import parse_tree
from ...tree_sitter_support.tree_walk import squashed, walk
from ..be_secure.uses import find_uses

TYPESCRIPT_TEST_CALLS = {"it", "test", "it.only", "test.only"}
CALLBACK_MARKERS = ("=>", "function")  # a real test passes its body as a function: test("name", () => ...)
PYTHON_TEST_PREFIX = "test"
RUST_TEST_ATTRIBUTE_END = "test]"  # #[test] and #[tokio::test], but not #[cfg(test)]

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

def count_typescript_tests(source):
    calls = [use for use in find_uses(source, TYPESCRIPT) if use.name in TYPESCRIPT_TEST_CALLS]

    return len([call for call in calls if any(marker in call.text for marker in CALLBACK_MARKERS)])

def count_tests_in_project(project):
    """Tests in every Python, Rust and TypeScript file, test folders included."""
    counters = {PYTHON: count_python_tests, RUST: count_rust_tests, TYPESCRIPT: count_typescript_tests}
    total = 0

    for path in project.files(*SUFFIX_LANGUAGE):
        total += counters[SUFFIX_LANGUAGE[path.suffix]](read_source(path))

    return total
