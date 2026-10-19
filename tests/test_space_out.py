from codequality.rules.space_out.paragraphs import find_blank_runs, find_paragraphs, is_judged

SAMPLE = "import os\nimport sys\nimport json\nimport re\nimport ast\nimport abc\nimport io\n\n\n\ndef f():\n    a = 1\n    b = 2\n\n    # one\n    # two\n    # three\n    # four\n    # five\n    # six\n    # seven\n\n    return a + b\n"


def test_paragraphs_and_blank_runs():
    lines = SAMPLE.splitlines()
    assert find_paragraphs(lines) == [(1, 7), (11, 3), (15, 7), (23, 1)]
    assert find_blank_runs(lines) == [(8, 3), (14, 1), (22, 1)]


def test_imports_and_comment_blocks_are_not_judged():
    lines = SAMPLE.splitlines()
    judged = [(first, length) for first, length in find_paragraphs(lines) if is_judged(lines, first, length)]
    assert (1, 7) not in judged and (15, 7) not in judged and (11, 3) in judged
