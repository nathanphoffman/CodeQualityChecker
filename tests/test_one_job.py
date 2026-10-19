from codequality.rules.one_job import has_joining_word, has_separate_jobs, is_too_complex
from codequality.rules.one_job.cohesion import count_job_groups
from codequality.rules.one_job.find_bodies import find_bodies

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
    source = "def busy(x):\n" + "".join(f"    if x == {n}:\n        return {n}\n" for n in range(7))
    (body,) = find_bodies(source, "python")
    assert is_too_complex(body)
