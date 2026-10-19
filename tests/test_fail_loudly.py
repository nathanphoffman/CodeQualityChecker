from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules
from codequality.rules.fail_loudly.python_handlers import python_handlers
from codequality.rules.fail_loudly.tree_handlers import tree_handlers

SILENT_PYTHON = '''
try:
    run()
except Exception:
    pass
try:
    run()
except:
    pass
try:
    run()
except KeyError:
    pass
'''

LOUD_PYTHON = '''
try:
    run()
except Exception as error:
    log(f"failed: {error}")
try:
    run()
except Exception:
    raise
try:
    run()
except ValueError:
    print("bad value")
def parses(text):
    try:
        int(text)
    except ValueError:
        return False
    return True
'''

SILENT_TYPESCRIPT = "try { run(); } catch (e) { }\npromise.catch(() => {});\npromise.catch((e) => null);\n"
LOUD_TYPESCRIPT = "try { run(); } catch (e) { console.error(e); }\ntry { run(); } catch (e) { throw e; }\npromise.catch(handle);\n"

SILENT_RUST = "fn f() { let _ = might_fail(); match r { Ok(v) => v, Err(_) => {} }; }"
LOUD_RUST = "fn f() { match r { Ok(v) => v, Err(e) => log(e) }; let x = run()?; }"


def loud_flags(handlers):
    return [handler.is_loud for handler in handlers if handler.is_catch]


def test_python_silent_and_loud_handlers():
    assert loud_flags(python_handlers(SILENT_PYTHON)) == [False, False, False]
    assert loud_flags(python_handlers(LOUD_PYTHON)) == [True, True, True, True]


def test_typescript_silent_and_loud_handlers():
    assert loud_flags(tree_handlers(SILENT_TYPESCRIPT, "typescript")) == [False, False, False]
    assert loud_flags(tree_handlers(LOUD_TYPESCRIPT, "typescript")) == [True, True, True]


def test_rust_silent_and_loud_handlers():
    assert loud_flags(tree_handlers(SILENT_RUST, "rust")) == [False, False]
    assert loud_flags(tree_handlers(LOUD_RUST, "rust")) == [True]
    assert len(tree_handlers(LOUD_RUST, "rust")) == 2  # the Err arm, and the ? that passes an error up


def test_hiding_calls_lower_the_score(tmp_path: Path):
    (tmp_path / "a.py").write_text("import contextlib\nwith contextlib.suppress(ValueError):\n    run()\nopen('f', errors='ignore')\n")
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert results["RULE-11-LOUD-ERRORS"].score == 0.0


def test_error_check_amount_has_a_wide_flat_top(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n" * 100)  # a small project with no error handling is fine
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert results["RULE-11-ERROR-CHECK-AMOUNT"].score == 1.0


def test_full_credit_range_is_one_check_per_216_to_1296_lines():
    from codequality.rules.comment_why.amount_checks import amount_score
    from codequality.rules.fail_loudly.limits import FULL_CREDIT_POWERS, LINES_PER_ERROR_CHECK

    lines = 6 ** 5  # 7776 lines
    expected = lines / LINES_PER_ERROR_CHECK
    for lines_per_check in (216, 400, 1296):
        assert abs(amount_score(lines / lines_per_check, expected, FULL_CREDIT_POWERS) - 1.0) < 1e-9
    assert amount_score(lines / 36, expected, FULL_CREDIT_POWERS) < 0.3  # one per 36 lines is now far too many
