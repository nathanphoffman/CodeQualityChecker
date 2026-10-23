from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules
from codequality.rules.rule_12_clean_up.python import analyze_python
from codequality.rules.rule_12_clean_up.tree_sitter import analyze_tree

MESSY_PYTHON = '''import os
import sys  # noqa: F401
from typing import List, Dict
import json as j


def work(data):
    leftover = 1
    used = 2
    _ignored = 3
    try:
        run()
    except ValueError as error:
        pass
    return used + data
    print("never runs")


def _never_called():
    pass


def _called():
    pass


_called()
D: Dict = {}
'''

MESSY_TYPESCRIPT = '''import def, { used, unusedName } from "m";
import * as ns from "n";
import "side-effect";
function work() {
  const leftover = 1;
  const kept = used;
  return kept;
  console.log("never runs");
}
function helper() {}
class K { private hidden() {} private shown() {} run() { this.shown(); } }
work(def);
'''

MESSY_RUST = '''use std::fmt;
use std::collections::{HashMap, HashSet};
pub use other::Exported;
use unused::Thing as Alias;

fn helper() {}

fn main() {
    let leftover = 1;
    let kept = HashMap::new();
    return;
    println!("never runs {:?}", kept);
}
'''

def test_python_findings():
    findings, usage = analyze_python(MESSY_PYTHON, is_package_init=False)
    assert findings.imports_total == 4 and findings.unused_imports == [1, 3, 4]  # os, List, json (sys has noqa; Dict is used)
    assert findings.unused_variables == [8, 13]  # leftover; the unused `except ... as error`
    assert findings.unreachable == [16]
    assert [name for name, _ in usage.private_definitions] == ["_never_called", "_called"]

def test_package_init_is_left_alone():
    assert analyze_python("import os\n", is_package_init=True)[0].imports_total == 0

def test_typescript_findings():
    findings, usage = analyze_tree(MESSY_TYPESCRIPT, "typescript")
    assert findings.imports_total == 4 and findings.unused_imports == [1, 2]  # unusedName and ns; def and used are used
    assert findings.unused_variables == [5]
    assert findings.unreachable == [8]
    assert sorted(name for name, _ in usage.private_definitions) == ["helper", "hidden", "shown", "work"]

def test_rust_findings():
    findings, usage = analyze_tree(MESSY_RUST, "rust")
    assert findings.unused_imports == [1, 2, 4]  # fmt, HashSet, Alias; HashMap is used; `pub use` is skipped
    assert findings.unused_variables == [9]
    assert findings.unreachable == [12]
    assert [name for name, _ in usage.private_definitions] == ["helper"]

def test_project_level_rules_see_unused_private_functions_plus_commented_code(tmp_path: Path):
    (tmp_path / "a.py").write_text(MESSY_PYTHON + "\n# total = price * quantity\n")
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert "_never_called" in results["RULE-12-UNUSED-PRIVATE-FUNCTIONS"].message
    assert results["RULE-12-COMMENTED-OUT-CODE"].score < 1.0
