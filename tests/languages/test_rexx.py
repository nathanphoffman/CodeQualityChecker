import warnings

from codequality.detect import detect
from codequality.language_parsers.rexx.parser import has_clean_rexx, parse_rexx
from codequality.language_parsers.tree_sitter.tree_walk import walk
from codequality.rules.rule_01_power_of_six.shared.find_functions import find_functions
from codequality.rules.rule_01_power_of_six.tree_sitter.text_calls import text_calls
from codequality.rules.rule_02_clear_names.shared.find_names import find_names
from codequality.rules.rule_03_simple_first.shared.find_clever import clever_constructs
from codequality.rules.rule_05_be_secure.shared.uses import find_uses
from codequality.rules.rule_07_magic_values.tree_sitter.tree_literals import tree_literals
from codequality.rules.rule_10_test_what_matters.count_tests import count_rexx_tests
from codequality.rules.rule_11_fail_loudly.tree_sitter.tree_handlers import tree_handlers
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree
from codequality.rules.rule_14_space_out.tree_sitter.text_spacing import text_gaps
from codequality.source_code import blank_out_text

REXX = """/* Report tool */
signal on error name failed
parse arg path, mode
query = "SELECT * FROM users WHERE name = " || path
address system "rm -rf " path
total = summarize(path)
call report total, mode
exit 0

summarize: procedure
  parse arg file
  count = 0
  unused = 5
  do forever
    line = linein(file)
    if line = '' then leave
    count = count + 100
  end
  return count
  say "never runs"

report: procedure expose seen
  parse arg value, how
  select
    when how = 'a' then say value
    otherwise
      say "other"
  end
  return

helper: procedure
  return 1

failed:
  say "failed at line" sigl
  exit 1

test_summarize:
  return summarize('x') = 0
"""

def types_in(source):
    return [node.type for node in walk(parse_rexx(source))]

def test_rexx_files_are_detected(tmp_path):
    (tmp_path / "run.rexx").write_text("say 1\n")
    assert "rexx" in detect(tmp_path).languages

def test_a_label_starts_a_routine_that_runs_to_the_next_label():
    routines = [node for node in walk(parse_rexx(REXX)) if node.type == "routine_definition"]
    assert sorted((r.child_by_field_name("name").text, r.start_point.row + 1, r.end_point.row + 1) for r in routines) == sorted([
        (b"summarize", 10, 20), (b"report", 22, 29), (b"helper", 31, 32), (b"failed", 34, 36), (b"test_summarize", 38, 39)])

def test_functions_are_found_with_one_argument_per_comma_separated_part():
    found = {info.name: (info.argument_count, info.line_count) for info in find_functions(REXX, "rexx")}
    assert found["summarize"] == (1, 11) and found["report"] == (2, 8) and found["helper"] == (0, 2)

def test_names_are_lower_case_because_rexx_ignores_case():
    assert {"summarize", "path", "mode", "count", "unused"} <= set(find_names(REXX, "rexx"))
    assert "total" in find_names("TOTAL = 1\n", "rexx")

def test_the_security_rules_see_sql_built_by_joining_plus_host_commands_with_variables():
    names = [use.name for use in find_uses(REXX, "rexx")]
    assert {"dynamic_string", "command", "say", "linein", "summarize"} <= set(names)
    assert "command" not in [use.name for use in find_uses('address system "ls -l"\n', "rexx")]

def test_literals_are_numbers_plus_strings_but_hex_strings_are_skipped():
    kinds = [(literal.kind, literal.value) for literal in tree_literals("x = 5 + 2.5\ny = 'a'\nz = '0A'x\n", "rexx")]
    assert sorted(kinds, key=str) == [("number", 2.5), ("number", 5), ("string", "a")]

def test_tests_are_labels_starting_with_test():
    assert count_rexx_tests(REXX) == 1
    assert count_rexx_tests("Test_one: \n return 1\n") == 1

def test_return_code_checks_plus_traps_are_judged_by_what_they_do():
    source = "'ls'\nif rc <> 0 then say 'failed'\nif rc <> 0 then nop\nsignal on error name oops\nexit 1\noops:\nsay 'bad'\n"
    catches = sorted((handler.line_number, handler.is_loud) for handler in tree_handlers(source, "rexx") if handler.is_catch)
    assert catches == [(2, True), (3, False), (4, True)]
    assert [handler.line_number for handler in tree_handlers(source, "rexx") if not handler.is_catch] == [5]

def test_cleanup_finds_unused_variables_dead_code_plus_helpers_nothing_calls():
    findings, usage = analyze_tree(REXX, "rexx")
    assert findings.unused_variables == [13]
    assert findings.unreachable == [20]
    assert sorted(name for name, _ in usage.private_definitions) == ["helper", "report", "summarize"]
    assert usage.references["helper"] == 1 and usage.references["summarize"] > 1

def test_variables_in_a_routine_without_procedure_are_shared_so_not_unused():
    findings, _ = analyze_tree("go:\n  shared = 1\n  return\n", "rexx")
    assert findings.unused_variables == []

def test_clever_constructs_are_interpret_signal_plus_value():
    found = clever_constructs("interpret 'x = 1'\nsignal done\nsignal on error\nx = value('name')\ndone:\n", "rexx")
    assert sorted(found) == [("indirect", 4), ("interpret", 1), ("signal", 2)]

def test_comments_plus_strings_are_blanked_even_when_comments_nest():
    assert blank_out_text("/* a /* b */ c */ x = 'it''s' // 2\n", "rexx") == "                  x =         // 2\n"

def test_prose_in_a_comment_is_not_code_but_an_assignment_is():
    assert has_clean_rexx("total = total + 1") and has_clean_rexx("if x then y = 2")
    assert not has_clean_rexx("the total is 5") and not has_clean_rexx("see (the docs); thanks")

def test_continued_lines_plus_operators_read_without_errors():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        parse_rexx("x = 1 +,\n  2\ny = \\a | b & c \\= d <> e >= f\ncall f a,\n  b\n")

def test_unreadable_source_warns_but_still_gives_a_tree():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert "source_file" in types_in("say 'unfinished\nend\n")

    assert any("syntax errors" in str(warning.message) for warning in caught)

def test_blank_lines_go_above_control_statements_plus_labels():
    spaced = "/* c */\nx = 1\n\nif x = 1 then do\n  say x\nend\nelse\n  say 2\n\nfoo:\n  return\n"
    assert text_gaps(spaced, "rexx").before_control_missing == []
    gaps = text_gaps("x = 1\nif x = 1 then do\n  say x\nend\nsay 2\nfoo:\n  return\n", "rexx")
    assert gaps.before_control_missing == [2, 6] and gaps.after_block_missing == [5]

def test_call_depth_follows_call_statements_plus_function_calls():
    calls = {name: set(called) for name, _, called in text_calls("main: \n  call One\n  return\none: \n  x = two()\n  return\ntwo: \n  return 1\n", "rexx")}
    assert calls == {"main": {"one"}, "one": {"two"}, "two": set()}
