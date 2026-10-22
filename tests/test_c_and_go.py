from codequality.detect import detect
from codequality.rules.rule_01_power_of_six.shared.find_functions import find_functions
from codequality.rules.rule_02_clear_names.shared.find_names import find_names
from codequality.rules.rule_05_be_secure.shared.uses import find_uses
from codequality.rules.rule_07_magic_values.tree_sitter.tree_literals import tree_literals
from codequality.rules.rule_10_test_what_matters.count_tests import count_c_tests, count_go_tests
from codequality.rules.rule_11_fail_loudly.tree_sitter.tree_handlers import tree_handlers
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree
from codequality.source_code import non_test_files

GO = """package main

import (
\t"fmt"
\t"os"
\tstr "strings"
)

func (s *Server) handle(a, b int) error {
\tdata, err := os.ReadFile("x")
\tif err != nil {
\t\treturn err
\t}

\tunused := 5
\tfmt.Println(data)
\treturn nil
\tfmt.Println("dead")
}

func quiet() {
\tif err := run(); err != nil {
\t}
\t_ = run()
}
"""

C = """#include <stdio.h>

static int helper(int count, char *label)
{
\tint total = count + 1;
\tint unused = 3;

\tif (label == NULL) {
\t\treturn -1;
\t}

\tprintf("%s", label);
\treturn total;
}

int test_helper(void)
{
\treturn 0;
}
"""

def test_c_and_go_files_are_detected(tmp_path):
    (tmp_path / "a.c").write_text("int main(void) { return 0; }\n")
    (tmp_path / "b.go").write_text("package main\n")
    assert {"c", "go"} <= detect(tmp_path).languages

def test_go_functions_and_methods_are_found_with_their_arguments():
    found = {info.name: info.argument_count for info in find_functions(GO, "go")}
    assert found == {"handle": 2, "quiet": 0}

def test_c_functions_are_found_and_void_is_not_an_argument():
    found = {info.name: info.argument_count for info in find_functions(C, "c")}
    assert found == {"helper": 2, "test_helper": 0}

def test_names_are_read_through_c_pointers_and_go_multiple_assignments():
    assert {"helper", "count", "label", "total"} <= set(find_names(C, "c"))
    assert {"handle", "a", "b", "data", "err", "unused"} <= set(find_names(GO, "go"))

def test_calls_are_named_with_dots_in_c_and_go():
    assert "os.ReadFile" in [use.name for use in find_uses(GO, "go")]
    assert "printf" in [use.name for use in find_uses(C, "c")]

def test_c_suffixes_and_go_import_paths_are_not_magic_values():
    numbers = [literal.value for literal in tree_literals("int x = 10UL;\n", "c")]
    assert numbers == [10]
    assert tree_literals('import "fmt"\n'.replace("import", "package main\nimport"), "go") == []

def test_tests_are_counted_by_name_in_c_and_go():
    assert count_c_tests(C) == 1
    assert count_go_tests("package a\nfunc TestOne(t *testing.T) {}\nfunc helper() {}\n") == 1

def test_go_error_checks_are_judged_by_what_the_block_does():
    catches = {handler.line_number: handler.is_loud for handler in tree_handlers(GO, "go") if handler.is_catch}
    assert catches == {11: True, 22: False, 24: False}  # returns err / empty block / `_ = run()`

def test_c_null_checks_count_as_error_handling():
    assert [handler.is_loud for handler in tree_handlers(C, "c")] == [True]

def test_go_cleanup_finds_unused_imports_variables_dead_code_and_private_functions():
    findings, usage = analyze_tree(GO, "go")
    assert findings.unused_imports == [6]
    assert findings.unused_variables == [15]
    assert findings.unreachable == [18]
    assert sorted(name for name, _ in usage.private_definitions) == ["handle", "quiet"]

def test_c_cleanup_finds_unused_variables_and_static_functions():
    findings, usage = analyze_tree(C, "c")
    assert findings.unused_variables == [6]
    assert [name for name, _ in usage.private_definitions] == ["helper"]

def test_go_test_files_are_left_out_of_non_test_rules(tmp_path):
    (tmp_path / "a.go").write_text("package a\n")
    (tmp_path / "a_test.go").write_text("package a\n")
    assert [path.name for path in non_test_files(detect(tmp_path), (".go",))] == ["a.go"]
