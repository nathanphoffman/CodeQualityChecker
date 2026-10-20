from pathlib import Path

from codequality.detect import detect
from codequality.rules.rule_01_power_of_six.call_depth.call_graph import call_depths
from codequality.rules.rule_01_power_of_six.shared.scoring import depth_credit

def depths_of(tmp_path: Path, filename: str, source: str):
    (tmp_path / filename).write_text(source)

    return sorted(call_depths(detect(tmp_path)).values())

def test_python_chain_depth_counts_each_function(tmp_path: Path):
    source = "def main():\n    child()\n\ndef child():\n    grandchild()\n\ndef grandchild():\n    print(1)\n"
    assert depths_of(tmp_path, "app.py", source) == [3]

def test_rust_calls_are_followed_and_loops_end(tmp_path: Path):
    source = "fn top() {\n    middle();\n}\n\nfn middle() {\n    bottom();\n}\n\nfn bottom() {\n    middle();\n}\n"
    assert depths_of(tmp_path, "lib.rs", source) == [3]

def test_deor_macro_runs_are_calls(tmp_path: Path):
    source = "macro inner\n    print(1)\n\nfn void outer()\n    macro_run inner\n"
    assert depths_of(tmp_path, "app.deor", source) == [2]

def test_depth_credit_slides_after_six():
    assert depth_credit(6) == 1.0
    assert 0.9 < depth_credit(7) < 1.0
    assert depth_credit(10) < 0.2

def test_deor_functions_and_nested_macros_all_count_as_levels(tmp_path: Path):
    source = ("fn void helper()\n    print(1)\n\nmacro middle\n    helper()\n\nfn void entry()\n    macro_run middle\n\n"
              "macro outer\n    macro inner\n        macro deepest\n            print(2)\n\n        macro_run deepest\n\n    macro_run inner\n\n"
              "fn void second()\n    macro_run outer\n")
    assert depths_of(tmp_path, "app.deor", source) == [3, 4]
