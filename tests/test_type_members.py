from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.models import Status
from codequality.registry import all_rules
from codequality.rules.rule_01_power_of_six.shared.find_types import find_types

# language -> (source, {type name: (fields, methods)})
TYPES_BY_LANGUAGE = {
    "python": ("class A:\n    x = 1\n    y: int = 2\n    def __init__(self): pass\n    def a(self): pass\n    def b(self): pass\n", {"A": (2, 2)}),
    "rust": ("struct A { x: i32, y: i32 }\nstruct B(i32, i32);\nenum E { P, Q, R }\nimpl A { fn f(&self) {} fn g(&self) {} }\nimpl B { fn h(&self) {} }\n"
             "trait T { fn h(&self); fn i(&self) {} }\n", {"A": (2, 2), "B": (2, 1), "E": (3, 0), "T": (0, 2)}),
    "typescript": ("class C { a = 1; b: number; m() {} constructor(){} get g() { return 1 } }\ninterface I { p: number; q(): void }\nenum E { A, B = 2 }\n"
                   "type T = { r: number }\nfunction Card({ title, body }: Props) { return 1 }\nconst Box = ({ a, b, c }: P) => 1;\nconst lower = ({ a }) => 1;\n",
                   {"C": (2, 2), "I": (1, 1), "E": (2, 0), "T": (1, 0), "Card": (2, 0), "Box": (3, 0)}),
    "go": ("package m\ntype A struct { x, y int; z string }\nfunc (a A) F() {}\nfunc (a *A) G() {}\ntype I interface { H(); J() }\n", {"A": (3, 2), "I": (0, 2)}),
    "c": ("struct S { int a, b; char c; };\nenum E { X, Y };\nunion U { int i; float f; };\nstruct S *pointer;\n", {"S": (3, 0), "E": (2, 0), "U": (2, 0)}),
    "csharp": ("class C { int a, b; public string P { get; set; } C() {} void M() {} }\nenum E { X, Y }\ninterface I { void Q(); }\nrecord R(int A, int B);\n",
               {"C": (3, 1), "E": (2, 0), "I": (0, 1), "R": (2, 0)}),
    "mojo": ("struct S:\n    var a: Int\n    var b: Int\n    fn m(self):\n        pass\n    fn __init__(inout self):\n        pass\n", {"S": (2, 1)}),
    "hare": ("type s = struct { a: int, b: int };\ntype e = enum { X, Y };\n", {"s": (2, 0), "e": (2, 0)}),
    "fortran": ("module m\ntype :: t\n  integer :: a, b\n  real :: c\ncontains\n  procedure :: p\nend type t\nend module m\n", {"t": (3, 1)}),
    "deor": ("struct Account\n    string owner\n    int balance\n\nenum Color\n    Red\n    Green\n", {"Account": (2, 0), "Color": (2, 0)}),
}

def grade(root: Path, filename: str, source: str, rule_id: str):
    (root / filename).write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def test_every_language_counts_fields_and_methods_per_type():
    for language, (source, expected) in TYPES_BY_LANGUAGE.items():
        found = {info.name: (info.fields, info.methods) for info in find_types(source, language)}

        assert found == expected, f"{language}: {found}"

def test_a_language_with_no_types_finds_none():
    assert find_types("say 1\n", "rexx") == []

def test_a_python_class_with_too_many_fields_loses_points(tmp_path: Path):
    fields = "".join(f"    field_{number} = {number}\n" for number in range(8))
    result = grade(tmp_path, "app.py", f"class Big:\n{fields}", "RULE-01-FIELDS")

    assert result.score < 1.0
    assert "Big (8)" in result.message

def test_methods_have_their_own_limit(tmp_path: Path):
    methods = "".join(f"    def method_{number}(self):\n        return {number}\n" for number in range(8))
    source = f"class Big:\n    only_field = 1\n{methods}"

    assert grade(tmp_path, "app.py", source, "RULE-01-FIELDS").status == Status.PASS
    assert grade(tmp_path, "app.py", source, "RULE-01-METHODS").score < 1.0

def test_six_fields_and_six_methods_is_fine(tmp_path: Path):
    source = "class Fine:\n" + "".join(f"    field_{number} = {number}\n" for number in range(6)) + "".join(f"    def method_{number}(self):\n        return {number}\n" for number in range(6))

    assert grade(tmp_path, "app.py", source, "RULE-01-FIELDS").status == Status.PASS
    assert grade(tmp_path, "app.py", source, "RULE-01-METHODS").status == Status.PASS

def test_impl_blocks_add_up_for_one_rust_type(tmp_path: Path):
    impls = "".join(f"impl Big {{ fn m{number}(&self) {{}} fn n{number}(&self) {{}} }}\n" for number in range(4))
    result = grade(tmp_path, "lib.rs", f"struct Big {{ a: i32 }}\n{impls}", "RULE-01-METHODS")

    assert result.score < 1.0
    assert "Big (8)" in result.message
