import ast

from ...python_support.parse_python import parse_python
from ...deor_support.structure.declarations import declarations_in
from ...deor_support.structure.tree import parse_deor
from ...source_code import DEOR, PYTHON, RUST, SUFFIX_LANGUAGE, TYPESCRIPT, read_source
from ...tree_sitter_support.parse_tree import parse_tree
from ...tree_sitter_support.tree_walk import squashed, walk
from ..be_secure.uses import find_uses

TYPESCRIPT_TEST_CALLS = {"it", "test", "it.only", "test.only"}
CALLBACK_MARKERS = ("=>", "function")  # a real test passes its body as a function: test("name", () => ...)
PYTHON_TEST_PREFIX = "test"
DEOR_EXPECTATION = "expect"  # a comment starting "expect:" or "expect-error:" in a Deor test example
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

def count_deor_tests(source):
    """Functions named test..., plus one for a file that states what it expects (# expect:, # expect-error: ...), which is how
    the Deor test runner reads a test example."""
    parsed = parse_deor(source)
    functions = [item for item in declarations_in(parsed.roots, ("fn",)) if item.name.startswith(PYTHON_TEST_PREFIX)]
    states_expectation = any(line.comment is not None and line.comment.strip().startswith(DEOR_EXPECTATION) for line in parsed.lines)

    return len(functions) + states_expectation

def count_tests_in_project(project):
    """Tests in every Python, Rust and TypeScript file, test folders included."""
    counters = {PYTHON: count_python_tests, RUST: count_rust_tests, TYPESCRIPT: count_typescript_tests, DEOR: count_deor_tests}
    total = 0

    for path in project.files(*SUFFIX_LANGUAGE):
        total += counters[SUFFIX_LANGUAGE[path.suffix]](read_source(path))

    return total
