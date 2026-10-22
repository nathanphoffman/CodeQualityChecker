from codequality.detect import detect
from codequality.rules.rule_02_clear_names.shared.find_names import find_names
from codequality.rules.rule_05_be_secure.shared.uses import find_uses
from codequality.rules.rule_10_test_what_matters.count_tests import count_hare_tests
from codequality.rules.rule_11_fail_loudly.tree_sitter.tree_handlers import tree_handlers
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree

def test_hare_files_are_detected(tmp_path):
    (tmp_path / "main.ha").write_text("export fn main() void = {};\n")
    assert "hare" in detect(tmp_path).languages

def test_hare_names_include_parameters_but_not_types():
    names = find_names("fn add(left: int, right: mytype) int = {\n\tlet total = left;\n};\n", "hare")
    assert {"add", "left", "right", "total"} <= set(names)
    assert "mytype" not in names

def test_hare_calls_are_named_with_dots():
    uses = find_uses('fn f() void = {\n\tfmt::println("hi")!;\n};\n', "hare")
    assert "fmt.println" in [use.name for use in uses]

def test_only_the_test_attribute_makes_a_hare_test():
    assert count_hare_tests("@test fn works() void = {};\nfn helper() void = {};\n@init fn setup() void = {};\n") == 1

def test_hare_error_cases_are_judged_by_what_they_do():
    silent = "fn f() void = {\n\tmatch (g()) {\n\tcase let e: fs::error =>\n\t\tvoid;\n\tcase => void;\n\t};\n};\n"
    loud = silent.replace("\t\tvoid;\n\tcase =>", '\t\tfmt::fatal("bad");\n\tcase =>')
    assert [handler.is_loud for handler in tree_handlers(silent, "hare")] == [False]
    assert [handler.is_loud for handler in tree_handlers(loud, "hare")] == [True]

def test_hare_cleanup_finds_unused_imports_variables_and_dead_code():
    source = "use fmt;\nuse os;\n\nfn f() void = {\n\tlet unused = 1;\n\treturn;\n\tfmt::println(\"x\")!;\n};\n"
    findings, _ = analyze_tree(source, "hare")
    assert findings.unused_imports == [2]
    assert findings.unused_variables == [5]
    assert findings.unreachable == [7]

def test_codequalityignore_skips_folders_and_everything_inside(tmp_path):
    (tmp_path / "vendor" / "deep").mkdir(parents=True)
    (tmp_path / "vendor" / "deep" / "copied.ha").write_text("fn f() void = {};\n")
    (tmp_path / "main.ha").write_text("fn g() void = {};\n")
    (tmp_path / ".codequalityignore").write_text("# not ours\nvendor/\n")
    assert [path.name for path in detect(tmp_path).files(".ha")] == ["main.ha"]
