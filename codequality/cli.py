from __future__ import annotations

import argparse
from pathlib import Path

from . import report
from .detect import detect
from .registry import all_rules

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codequality", description="Grade a project against RULES.md")
    parser.add_argument("path", type=Path, nargs="?", default=Path("."), help="project root to check (default: current directory)")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--only", action="append", default=[], help="only run rules whose ID starts with this, e.g. RULE-03 (repeatable)")
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument("--quick", action="store_true", help="only each rule's score and the total")
    detail.add_argument("--full", action="store_true", help="every check with what it looks for, what was found and how to fix it")
    parser.add_argument("--min-score", type=float, default=None, help="exit 1 if overall score is below this")

    args = parser.parse_args(argv)

    root = args.path.resolve()

    if not root.is_dir():
        parser.error(f"{root} is not a directory")

    project = detect(root)
    rules = [rule for rule in all_rules() if not args.only or rule.id.startswith(tuple(args.only))]
    results = report.run(project, rules)

    if args.json:
        print(report.to_json(project, results))
    elif args.quick:
        report.print_quick(project, results)
    elif args.full:
        report.print_full(project, results)
    else:
        report.print_text(project, results)

    if args.min_score is not None and report.overall_score(results) < args.min_score:
        return 1

    return 0
