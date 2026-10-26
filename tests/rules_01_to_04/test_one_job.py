from codequality.rules.rule_04_one_job import has_flag_parameter, has_joining_word, has_separate_jobs, is_too_complex, is_too_nested
from codequality.rules.rule_04_one_job.shared.cohesion import count_job_groups
from codequality.rules.rule_04_one_job.shared.find_bodies import find_bodies

TWO_JOBS = {
    "python": """def process(order, report):
    total = order.price
    tax = total * 2
    order.cost = total + tax
    title = report.name
    report.header = title
""",

    "rust": """fn process(order: &mut Order, report: &mut Report) {
    let total = order.price;
    let tax = total * 2;
    order.cost = total + tax;
    let title = report.name;
    report.header = title;
}
""",

    "typescript": """function process(order: Order, report: Report) {
  const total = order.price;
  const tax = total * 2;
  order.cost = total + tax;
  const title = report.name;
  report.header = title;
}
""",
}

ONE_JOB_PYTHON = """def tidy(a):
    b = a + 1
    c = b * 2
    d = c - a
    return d
"""

def test_groups_split_when_nothing_is_shared():
    assert count_job_groups([{"a", "b"}, {"c"}, {"b"}]) == 2

def test_groups_ignore_statements_without_locals():
    assert count_job_groups([{"a"}, set(), {"a"}]) == 1

def test_separate_jobs_found_in_every_language():
    for language, source in TWO_JOBS.items():
        (body,) = find_bodies(source, language)
        assert has_separate_jobs(body), language

def test_connected_statements_are_one_job():
    (body,) = find_bodies(ONE_JOB_PYTHON, "python")
    assert not has_separate_jobs(body)

def test_joining_word_in_name():
    (body,) = find_bodies("def validate_and_save(x):\n    return x\n", "python")
    assert has_joining_word(body)

def test_complexity_counts_branches():
    source = "def busy(x):\n" + "".join(f"    if x == {number}:\n        return {number}\n" for number in range(7))
    (body,) = find_bodies(source, "python")
    assert is_too_complex(body)

NESTED_FOUR_DEEP = {
    "python": "def f(a):\n    if a:\n        for b in a:\n            while b:\n                if b:\n                    return 1\n",
    "rust": "fn f(a: i32) {\n    if a > 0 { for b in 0..a { while true { if b > 1 { return; } } } }\n}\n",
    "typescript": "function f(a: number) {\n  if (a) { for (const b of [a]) { while (b) { if (b) { return 1; } } } }\n}\n",
}

NESTED_THREE_DEEP_WITH_ELSE_IF = {
    "python": "def f(a):\n    if a == 1:\n        return 1\n    elif a == 2:\n        return 2\n    elif a == 3:\n        for b in a:\n            if b:\n                return b\n",
    "typescript": "function f(a: number) {\n  if (a === 1) { return 1; } else if (a === 2) { return 2; } else if (a === 3) { for (const b of [a]) { if (b) { return b; } } }\n}\n",
    "c": "int f(int a) {\n  if (a == 1) { return 1; } else if (a == 2) { return 2; } else if (a == 3) { for (;;) { if (a) { return a; } } }\n  return 0;\n}\n",
}

def test_nesting_over_three_is_flagged_in_every_language():
    for language, source in NESTED_FOUR_DEEP.items():
        (body,) = find_bodies(source, language)
        assert body.max_nesting == 4 and is_too_nested(body), language

def test_else_if_is_not_another_level():
    for language, source in NESTED_THREE_DEEP_WITH_ELSE_IF.items():
        (body,) = find_bodies(source, language)
        assert body.max_nesting == 3 and not is_too_nested(body), language

def test_inner_functions_are_measured_on_their_own():
    source = "function f(a: number) {\n  if (a) {\n    return [1].map((b) => {\n      if (b) { if (a) { return 1; } }\n      return 0;\n    });\n  }\n}\n"
    assert [body.max_nesting for body in find_bodies(source, "typescript")] == [1, 2]

def test_boolean_flag_parameters_are_found():
    flags = {
        "python": "def f(data, strict: bool):\n    return data\n",
        "python ": "def f(data, strict=False):\n    return data\n",
        "typescript": "function f(data: string, strict: boolean) {\n  return data;\n}\n",
        "rust": "fn f(data: i32, strict: bool) -> i32 {\n    data\n}\n",
        "go": "func f(data int, strict bool) int {\n  return data\n}\n",
        "c": "int f(int data, bool strict) {\n  return data;\n}\n",
    }

    for language, source in flags.items():
        (body,) = find_bodies(source, language.strip())
        assert has_flag_parameter(body), language

def test_lone_boolean_and_props_objects_are_not_flags():
    for language, source in {
        "python": "def set_enabled(on: bool):\n    return on\n",
        "typescript": "function Panel({ open, name }: { open: boolean; name: string }) {\n  return open;\n}\n",
        "rust": "fn f(items: Vec<bool>, count: i32) -> i32 {\n    count\n}\n",
    }.items():
        (body,) = find_bodies(source, language)
        assert not has_flag_parameter(body), language
