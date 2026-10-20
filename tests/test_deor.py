from pathlib import Path

from codequality.detect import detect
from codequality.rules.power_of_six.find_functions import find_functions
from codequality.rules.power_of_six.measure import functions_per_file, per_function

SOURCE = """macro say_hello
    print(hello)

unsafe_macro start_timer
    int _start = now_ms()
    int _extra = 1

fn void greet(string name, int count)
    macro local_one
        print(name)

    macro_run local_one
    macro_run say_hello

fn int wrapped(
    int one,
    int two
)
    one + two
"""

def test_deor_functions_and_macros_are_found():
    found = {info.name: info for info in find_functions(SOURCE, "deor")}
    assert list(found) == ["macro say_hello", "macro start_timer", "greet", "macro local_one", "wrapped"]
    assert (found["macro say_hello"].argument_count, found["macro say_hello"].line_count) == (0, 2)
    assert found["macro start_timer"].line_count == 3
    assert (found["greet"].argument_count, found["greet"].line_count) == (2, 6)  # the local macro is part of greet's body
    assert (found["wrapped"].argument_count, found["wrapped"].line_count) == (2, 5)

def test_deor_files_are_judged_by_the_function_rules(tmp_path: Path):
    (tmp_path / "app.deor").write_text(SOURCE)
    (tmp_path / "tabs.deor").write_text("macro tabbed\n\ta as 1\n\tb as 2\n")
    project = detect(tmp_path)
    assert project.languages == {"deor"}
    assert functions_per_file(project) == {"app.deor": 5, "tabs.deor": 1}
    assert per_function(project, "line_count")["tabs.deor:1 macro tabbed"] == 3

FULL = """import "lib/string.deor"

struct Account
    string owner
    int balance

unsafe_macro timer_start
    int _timer_start = n_now_ms()

fn int find_account(accountList accounts, string wanted)
    int missing = 0 - 1
    unused_value as 42
    password as "hunter2hunter2"
    for idx in range(count)
        (owner) in accounts
        if owner is wanted and wanted is not valid
            return idx
    # print(missing)
    return missing
    print("never")

fn void log_it(string msg)
    string line = s_join(["SELECT * FROM users WHERE name = ", msg])
    crash(msg)
    Roll best
    if best is not valid
        print(msg)
    rust
        let _ = std::fs::remove_file("x");
        unsafe { run(); }
"""

def test_deor_names_include_parameters_fields_and_variables():
    from codequality.rules.clear_names.find_names import find_names

    names = find_names(FULL, "deor")
    assert {"Account", "owner", "balance", "find_account", "accounts", "wanted", "missing", "idx", "msg", "best"} <= set(names)
    assert "run" not in names and "remove_file" not in names  # inside a rust block

def test_deor_bodies_count_branches_and_variables():
    from codequality.rules.one_job.find_bodies import find_bodies

    bodies = {body.name: body for body in find_bodies(FULL, "deor")}
    assert bodies["find_account"].branch_count == 3  # for, if, and
    assert bodies["macro timer_start"].branch_count == 0

def test_deor_literals_skip_imports_rust_blocks_and_constants():
    from codequality.rules.magic_values.tree_literals import tree_literals

    found = [(use.kind, use.value, use.in_constant) for use in tree_literals(FULL + "\nfn void run()\n    const int MAX = 5\n", "deor")]
    assert ("number", -1, False) not in found and ("number", 0, False) in found  # `0 - 1` is a subtraction
    assert ("number", 42, False) in found and ("number", 5, True) in found
    assert not any(kind == "string" and value == "lib/string.deor" for kind, value, _ in found)

def test_deor_uses_find_calls_built_sql_and_rust_blocks_at_their_lines():
    from codequality.rules.be_secure.uses.tree_uses import tree_uses

    uses = {(use.name, use.line_number) for use in tree_uses(FULL, "deor")}
    assert ("crash", 24) in uses and ("dynamic_string", 23) in uses and ("unsafe", 30) in uses

def test_deor_error_handlers_crashes_checks_and_rust_blocks():
    from codequality.rules.fail_loudly.tree_handlers import tree_handlers

    found = [(handler.line_number, handler.is_catch, handler.is_loud) for handler in tree_handlers(FULL, "deor")]
    assert (24, False, True) in found  # crash
    assert (26, True, True) in found  # is not valid check that prints
    assert (29, True, False) in found  # `let _ =` in a rust block

def test_deor_cleanup_finds_unread_variables_and_unreachable_code():
    from codequality.rules.clean_up.tree_checks import analyze_tree

    findings, _ = analyze_tree(FULL, "deor")
    assert findings.unused_variables == [12, 13, 23]
    assert findings.unreachable == [20]

def test_deor_spacing_wants_blank_lines_before_control_and_after_blocks():
    from codequality.rules.space_out.deor_spacing import deor_gaps

    source = "fn void run()\n    int one = 1\n    if one is 1\n        print(one)\n    print(one)\n\n    return\n"
    control_total, control_missing, block_total, block_missing = deor_gaps(source)
    assert control_missing == [3] and block_missing == [5]

def test_deor_comments_and_commented_out_code():
    from codequality.rules.comment_why.extract import tree_comments
    from codequality.rules.comment_why.judging.signals import is_commented_out_code

    comments = tree_comments(FULL, "deor")
    assert [comment.text for comment in comments] == ["print(missing)"]
    assert is_commented_out_code("print(missing)", "deor") and not is_commented_out_code("loops over every account", "deor")

def test_deor_clever_is_unsafe_macros_and_rust_blocks():
    from codequality.rules.simple_first.find_clever import clever_constructs

    assert clever_constructs(FULL, "deor") == [("unsafe_macro", 7)]

def test_deor_tests_and_secrets():
    from codequality.rules.be_secure.secrets import secret_line_numbers
    from codequality.rules.test_what_matters.count_tests import count_deor_tests

    assert count_deor_tests("fn void test_one()\n    print(one)\n\n# expect:\n# 1\n") == 2
    assert secret_line_numbers('password as "hunter2hunter2"\n') == [1]
