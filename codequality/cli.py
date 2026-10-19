from __future__ import annotations

import argparse
from pathlib import Path

from . import report
from .detect import detect
from .registry import all_rules


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="codequality", description="Grade a project against RULES.md")
    p.add_argument("path", type=Path, help="project root to check")
    p.add_argument("--json", action="store_true", help="output JSON")
    p.add_argument("--only", action="append", default=[], help="only run rules whose ID starts with this, e.g. RULE-03 (repeatable)")
    p.add_argument("--min-score", type=float, default=None, help="exit 1 if overall score is below this")
    args = p.parse_args(argv)

    root = args.path.resolve()
    if not root.is_dir():
        p.error(f"{root} is not a directory")

    project = detect(root)
    rules = [r for r in all_rules() if not args.only or r.id.startswith(tuple(args.only))]
    results = report.run(project, rules)
    if args.json:
        print(report.to_json(project, results))
    else:
        report.print_text(project, results)

    if args.min_score is not None and report.overall_score(results) < args.min_score:
        return 1
    return 0
