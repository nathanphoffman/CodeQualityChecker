from codequality.detect import detect
from codequality.rules.rule_01_power_of_six.shared.find_functions import find_functions
from codequality.rules.rule_01_power_of_six.tree_sitter.text_calls import text_calls
from codequality.rules.rule_02_clear_names.shared.find_names import find_names
from codequality.rules.rule_05_be_secure.shared.uses import find_uses
from codequality.rules.rule_07_magic_values.tree_sitter.tree_literals import tree_literals
from codequality.rules.rule_10_test_what_matters.count_tests import count_fortran_tests, count_mojo_tests
from codequality.rules.rule_11_fail_loudly.tree_sitter.tree_handlers import tree_handlers
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree
from codequality.rules.rule_14_space_out.tree_sitter.text_spacing import text_gaps

MOJO = """from std.collections import List as Items, Dict

fn _hidden(x: Int) -> Int:
    var unused = 5
    var kept = x + 1
    if kept > 3:
        raise Error("big")
    try:
        _hidden(kept)
    except e:
        pass
    return kept
    print("dead")

struct Point:
    fn norm(self, scale: Int) -> Int:
        return scale

def test_point():
    print(Point().norm(2))
"""

FORTRAN = """module geometry
  use iso_fortran_env, only: real64, int32
  implicit none
  real(real64), parameter :: pi = 3.14159_real64

contains

  function Area(radius) result(total)
    real(real64), intent(in) :: radius
    real(real64) :: total
    integer :: unused_count
    total = pi * RADIUS ** 2
    open(unit=10, file="x.txt", iostat=ios)
    if (ios /= 0) stop "cannot open"
    return
    print *, "dead"
  end function Area

  subroutine test_area()
    call helper(2)
  contains
    subroutine helper(n)
      integer, intent(in) :: n
      print *, n
    end subroutine helper
  end subroutine test_area

end module geometry
"""

def test_mojo_plus_fortran_files_are_detected(tmp_path):
    (tmp_path / "a.mojo").write_text("fn main():\n    pass\n")
    (tmp_path / "b.f90").write_text("program p\nend program p\n")
    assert {"mojo", "fortran"} <= detect(tmp_path).languages

def test_functions_are_measured_from_the_syntax_tree():
    mojo = {info.name: (info.argument_count, info.line_count) for info in find_functions(MOJO, "mojo")}
    assert mojo["norm"] == (1, 2)  # self is not an argument
    fortran = {info.name: info.argument_count for info in find_functions(FORTRAN, "fortran")}
    assert fortran == {"area": 1, "test_area": 0, "helper": 1}  # names ignore case

def test_fortran_call_without_parentheses_is_a_call():
    calls = {name: called for name, _, called in text_calls(FORTRAN, "fortran")}
    assert "helper" in calls["test_area"]

def test_names_are_read_from_mojo_patterns_plus_fortran_declarators():
    assert {"_hidden", "kept", "scale", "Point"} <= set(find_names(MOJO, "mojo"))
    assert {"Area", "radius", "unused_count", "pi"} <= set(find_names(FORTRAN, "fortran"))

def test_calls_plus_statements_are_named_for_the_security_rules():
    assert "print" in [use.name for use in find_uses(MOJO, "mojo")]
    assert {"open", "print"} <= {use.name for use in find_uses(FORTRAN, "fortran")}

def test_fortran_kinds_plus_mojo_prefixes_do_not_hide_numbers_plus_strings():
    assert sorted(literal.value for literal in tree_literals("program p\nx = 1.5_dp\ny = 2d3\nend program p\n", "fortran")) == [1.5, 2000.0]
    assert [literal.value for literal in tree_literals('fn f():\n    var s = f"id {1}"\n', "mojo") if literal.kind == "string"] == ["id {1}"]

def test_tests_are_counted_by_name():
    assert count_mojo_tests(MOJO) == 1
    assert count_fortran_tests(FORTRAN) == 1

def test_mojo_except_plus_fortran_status_checks_are_judged_by_what_they_do():
    assert [(handler.is_catch, handler.is_loud) for handler in tree_handlers(MOJO, "mojo") if handler.is_catch] == [(True, False)]
    fortran = {handler.is_catch: handler.is_loud for handler in tree_handlers(FORTRAN, "fortran")}
    assert fortran == {True: True, False: True}

def test_mojo_cleanup():
    findings, usage = analyze_tree(MOJO, "mojo")
    assert findings.unused_imports == [1, 1]
    assert findings.unused_variables == [4]
    assert findings.unreachable == [13]
    assert [name for name, _ in usage.private_definitions] == ["_hidden"]

def test_fortran_cleanup_ignores_case_plus_end_line_names():
    findings, usage = analyze_tree(FORTRAN, "fortran")
    assert findings.unused_imports == [2]  # int32
    assert findings.unused_variables == [11]
    assert findings.unreachable == [16]
    assert [name for name, _ in usage.private_definitions] == ["helper"]

def test_mojo_blocks_end_where_the_indentation_drops():
    gaps = text_gaps("fn f():\n    if x:\n        y()\n    z()\n", "mojo")
    assert gaps.after_block_total == 1 and gaps.after_block_missing == [4]

def test_fortran_blocks_end_at_end_lines():
    gaps = text_gaps("subroutine s()\n  do i = 1, 3\n    call f(i)\n  end do\n  call g()\nend subroutine s\n", "fortran")
    assert gaps.after_block_missing == [5]
