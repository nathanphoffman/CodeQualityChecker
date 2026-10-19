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
