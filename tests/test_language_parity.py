from codequality.rules.be_secure.secrets import secret_line_numbers
from codequality.rules.clear_names.find_names import find_names
from codequality.rules.space_out.text_spacing import text_gaps

def test_parameters_count_as_names_in_every_language():
    assert {"a", "b"} <= set(find_names("def f(a, b):\n    return a\n", "python"))
    assert {"a", "b"} <= set(find_names("function f(a: number, b?: string) {}\n", "typescript"))
    assert {"a", "b", "c"} <= set(find_names("const g = c => c;\nfunction f(a: number, { b }: Options) {}\n", "typescript"))
    assert {"a", "b", "c"} <= set(find_names("fn f(a: i32, mut b: i32) { let g = |c| c; }\n", "rust"))

def test_secrets_are_found_behind_a_type_annotation():
    assert secret_line_numbers('const PASSWORD: &str = "hunter2hunter2";\n') == [1]
    assert secret_line_numbers('const password: string = "hunter2hunter2";\n') == [1]
    assert secret_line_numbers('password: str = "hunter2hunter2"\n') == [1]
    assert secret_line_numbers('const password: string = process.env.PASSWORD;\n') == []

def test_rust_value_at_the_end_of_a_block_counts_as_a_return():
    rust = "fn f(x: i32) -> i32 {\n    let y = x + 1;\n    y\n}\n"
    assert text_gaps(rust, "rust").before_control_missing == [3]
    assert text_gaps(rust, "typescript").before_control_missing == []

def test_typescript_arrow_functions_are_definitions():
    typescript = "const a = 1;\nconst f = (x: number): number => {\n  return x;\n};\nconst g = items.map((i) => {\n  return i;\n});\n"
    assert text_gaps(typescript, "typescript").before_control_missing == [2]
