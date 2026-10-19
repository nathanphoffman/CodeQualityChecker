from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

PYTHON_COPY = '''
def first(orders, rate):
    total = 0
    for order in orders:
        total += order.price * order.quantity
    tax = total * rate
    return total + tax

def second(items, percent):
    sum_so_far = 0
    for item in items:
        sum_so_far += item.price * item.quantity
    extra = sum_so_far * percent
    return sum_so_far + extra
'''

PYTHON_PARTIAL_COPY = '''
def alpha(orders, rate):
    total = 0
    for order in orders:
        total += order.price * order.quantity
    tax = total * rate
    fee = tax + total
    print("first")
    return total + tax

def beta(items, percent):
    log(items)
    sum_so_far = 0
    for item in items:
        sum_so_far += item.price * item.quantity
    extra = sum_so_far * percent
    charge = extra + sum_so_far
    return extra
'''

TYPESCRIPT_COPY = '''
function first(orders: Order[], rate: number) {
  let total = 0;
  for (const order of orders) { total += order.price * order.quantity; }
  const tax = total * rate;
  return total + tax;
}
function second(items: Order[], percent: number) {
  let sum = 0;
  for (const item of items) { sum += item.price * item.quantity; }
  const extra = sum * percent;
  return sum + extra;
}
'''

RUST_COPY = '''
fn first(orders: &[Order], rate: f64) -> f64 {
    let mut total = 0.0;
    for order in orders { total += order.price * order.quantity; }
    let tax = total * rate;
    total + tax
}
fn second(items: &[Order], percent: f64) -> f64 {
    let mut sum = 0.0;
    for item in items { sum += item.price * item.quantity; }
    let extra = sum * percent;
    sum + extra
}
'''

DIFFERENT = '''
def first(orders, rate):
    total = 0
    for order in orders:
        total += order.price * order.quantity
    tax = total * rate
    return total + tax

def second(items, percent):
    sum_so_far = 0
    for item in items:
        sum_so_far -= item.price * item.quantity
    extra = sum_so_far * percent
    return sum_so_far + extra
'''

def grade(root: Path, filename: str, source: str, rule_id: str):
    (root / filename).write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def test_renamed_copies_of_functions_are_found_in_every_language(tmp_path: Path):
    for filename, source in (("a.py", PYTHON_COPY), ("a.ts", TYPESCRIPT_COPY), ("a.rs", RUST_COPY)):
        folder = tmp_path / filename.replace(".", "_")
        folder.mkdir()
        result = grade(folder, filename, source, "RULE-06-DUPLICATE-FUNCTIONS")
        assert result.score == 0.5, filename

        assert "second" in result.message, filename

def test_copied_block_inside_different_functions_is_found(tmp_path: Path):
    result = grade(tmp_path, "a.py", PYTHON_PARTIAL_COPY, "RULE-06-DUPLICATE-BLOCKS")
    assert result.score < 1.0

def test_a_changed_operator_is_not_a_copy(tmp_path: Path):
    assert grade(tmp_path, "a.py", DIFFERENT, "RULE-06-DUPLICATE-FUNCTIONS").score == 1.0
