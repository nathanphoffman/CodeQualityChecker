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

def test_next_project_with_tsx(tmp_path):
    from codequality import report
    from codequality.detect import detect
    from codequality.registry import all_rules

    (tmp_path / "package.json").write_text('{"dependencies": {"next": "14"}}')
    (tmp_path / ".env").write_text("NEXT_PUBLIC_API_TOKEN=abc\n")
    (tmp_path / "card.tsx").write_text('export default function Card() {\n  return <img src="/a.png" />;\n}\n')
    (tmp_path / "route.ts").write_text("export function GET() {\n  return 1;\n}\n")
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert results["TS-NEXT-001"].score == 0.0
    assert results["TS-NEXT-002"].score == 0.0
    assert "GET" not in results["RULE-02-NAME-LENGTH"].message

def test_gitignored_files_are_skipped(tmp_path):
    import subprocess

    from codequality.detect import detect

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("generated/\n*.skip.ts\n")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "big.ts").write_text("export const a = 1;\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.ts").write_text("export const b = 1;\n")
    (tmp_path / "a.skip.ts").write_text("export const c = 1;\n")
    (tmp_path / "kept.ts").write_text("export const d = 1;\n")
    assert [path.name for path in detect(tmp_path).files(".ts")] == ["kept.ts"]

def test_going_over_six_slides_the_credit_down():
    from codequality.rules.power_of_six.scoring import function_length_credit, strict_credit

    assert strict_credit(6) == 1.0 and 0.97 < strict_credit(7) < strict_credit(6)
    assert strict_credit(7) > strict_credit(8) > strict_credit(12) > strict_credit(36) > strict_credit(100)
    assert strict_credit(100) < 0.01
    assert abs(function_length_credit(36) - 0.5) < 1e-9 and function_length_credit(100) < 0.2
