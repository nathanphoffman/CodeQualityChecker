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

def test_python_blank_line_gaps():
    from codequality.rules.space_out.python_spacing import python_gaps

    source = "def f(x):\n    y = 1\n    if x:\n        return y\n    # note\n    for i in x:\n        pass\n    total = [\n        1,\n    ]\n    z = 2\n    return z\n"
    gaps = python_gaps(source)
    assert gaps.before_control_missing == [3, 5, 12]  # the if, the for (and its note), the final return; the first return is first in its block
    assert gaps.before_control_total == 3
    assert gaps.after_block_missing == [5, 8, 11]  # after the if block, after the for block, and after the multi-line list

def test_python_gaps_are_zero_for_well_spaced_code():
    from codequality.rules.space_out.python_spacing import python_gaps

    source = "def f(x):\n    y = 1\n\n    if x:\n        return y\n\n    return 2\n"
    gaps = python_gaps(source)
    assert gaps.before_control_missing == [] and gaps.after_block_missing == []

def test_blank_lines_inside_strings_are_not_double_blank_lines():
    from codequality.rules.space_out.python_spacing import python_string_lines

    lines = "x = '''a\n\n\nb'''\n\n\ny = 1\n".splitlines()
    assert find_blank_runs(lines, python_string_lines("\n".join(lines))) == [(5, 2)]

def test_text_gaps_for_typescript_and_rust():
    from codequality.rules.space_out.text_spacing import text_gaps

    typescript = "function f(x) {\n  const y = 1;\n  if (x) {\n    return y;\n  }\n  return 2;\n}\n"
    gaps = text_gaps(typescript, "typescript")
    assert gaps.before_control_missing == [3, 6]  # the if and the last return; the first return is first in its block
    assert gaps.after_block_missing == [6]  # the closing brace of the if is followed by a statement
    rust = "fn f() {\n    let a = 1;\n\n    loop {\n        break;\n    }\n\n    match a {\n        1 => (),\n        _ => (),\n    }\n}\n"
    assert text_gaps(rust, "rust").before_control_missing == [] and text_gaps(rust, "rust").after_block_missing == []
