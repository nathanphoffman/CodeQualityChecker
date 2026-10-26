from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

PYTHON = '''
MAX_RETRIES = 5
LOW, HIGH = 10, 90
SECONDS = {"minute": 60, "hour": 3600}

def work(count):
    """Uses 7 in the docstring."""
    half = count / 2
    first = count - 1
    return count * 86400 + half + first + -42
'''

TYPESCRIPT = '''
const MAX_RETRIES = 5;
function work(count: number) {
  return count * 86400 + 0 + 1;
}
'''

RUST = '''
const MAX_RETRIES: u32 = 5;
fn work(count: u32) -> u32 {
    count * 86_400 + 0xFF + 1u32
}
'''

REPEATED = "".join(f'def f{n}():\n    return "same-text-here"\n' for n in range(3))

def grade(root: Path, filename: str, source: str, rule_id: str):
    (root / filename).write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def test_only_unnamed_python_numbers_are_flagged(tmp_path: Path):
    result = grade(tmp_path, "a.py", PYTHON, "RULE-07-MAGIC-NUMBERS")
    assert "86400" in result.message and "-42" in result.message
    assert result.message.startswith("2 of ")

def test_typescript_plus_rust_numbers(tmp_path: Path):
    typescript = grade(tmp_path, "a.ts", TYPESCRIPT, "RULE-07-MAGIC-NUMBERS")
    assert typescript.message.startswith("1 of ") and "86400" in typescript.message
    other = tmp_path / "rust"
    other.mkdir()
    rust = grade(other, "a.rs", RUST, "RULE-07-MAGIC-NUMBERS")

    assert rust.message.startswith("2 of ") and "86400" in rust.message and "255" in rust.message

def test_repeated_strings_are_flagged(tmp_path: Path):
    result = grade(tmp_path, "a.py", REPEATED, "RULE-07-REPEATED-STRINGS")
    assert "same-text-here" in result.message and result.score == 0.0

TYPE_KEYWORDS = "".join(f"function f{n}(x: string): string[] {{ return [x]; }}\n" for n in range(3))

def test_typescript_string_type_is_not_a_repeated_string(tmp_path: Path):
    result = grade(tmp_path, "a.ts", TYPE_KEYWORDS, "RULE-07-REPEATED-STRINGS")
    assert result.message == "no strings found" and result.score == 1.0

LAYOUT = '''
export const Chart = () => (
  <svg viewBox="0 0 640 480">
    <circle cx={320} cy={240} r={77} />
    <div style={{ marginTop: 13, width: 421 }} />
  </svg>
);
export function draw(ctx: CanvasRenderingContext2D) {
  ctx.moveTo(37, 91);
  ctx.arc(55, 66, 29, 0, 3.14);
}
'''

def test_svg_style_and_canvas_numbers_are_not_flagged(tmp_path: Path):
    result = grade(tmp_path, "chart.tsx", LAYOUT, "RULE-07-MAGIC-NUMBERS")
    assert result.message == "" and result.score == 1.0

def test_numbers_outside_layout_are_still_flagged(tmp_path: Path):
    source = LAYOUT + "export const wait = (ms: number) => ms * 4242;\n"
    result = grade(tmp_path, "chart.tsx", source, "RULE-07-MAGIC-NUMBERS")
    assert "4242" in result.message

def test_number_in_two_files_is_a_shared_number(tmp_path: Path):
    (tmp_path / "a.py").write_text("def a(x):\n    return x * 7919 + 100 + 2\n")
    result = grade(tmp_path, "b.py", "def b(x):\n    return x + 7919 + 100 + 2\n", "RULE-07-SHARED-NUMBERS")
    assert "7919 (2 files)" in result.message and "100" not in result.message

def test_number_repeated_in_one_file_is_not_shared(tmp_path: Path):
    result = grade(tmp_path, "a.py", "def a(x):\n    return x * 7919 + 7919\n", "RULE-07-SHARED-NUMBERS")
    assert result.score == 1.0 and result.message == ""
