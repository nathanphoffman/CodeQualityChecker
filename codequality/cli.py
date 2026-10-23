from __future__ import annotations

import argparse
from pathlib import Path

from . import report
from .detect import detect
from .fix_spacing import fix_spacing
from .registry import all_rules

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codequality", description="Grade a project against RULES.md")
    parser.add_argument("path", type=Path, nargs="?", default=Path("."), help="project root to check (default: current directory)")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--only", action="append", default=[], help="only run rules whose ID starts with this, e.g. RULE-03 (repeatable)")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATTERN", help="skip files and folders whose name or relative path matches this wildcard, e.g. '*out.rs*' (repeatable)")
    parser.add_argument("--fix-spacing", action="store_true", help="add the missing blank lines and remove doubled ones (RULE-14) in place, then exit")
    parser.add_argument("--min-score", type=float, default=None, help="exit 1 if overall score is below this")
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument("--quick", action="store_true", help="only each rule's score and the total")
    detail.add_argument("--full", action="store_true", help="every check with what it looks for, what was found and how to fix it")

    return parser

def print_results(args, project, results):
    """Prints in the one format the flags ask for; plain text is the default."""
    if args.json:
        print(report.to_json(project, results))
    elif args.quick:
        report.print_quick(project, results)
    elif args.full:
        report.print_full(project, results)
    else:
        report.print_text(project, results)

def run_spacing_fix(project) -> int:
    changed = fix_spacing(project)
    print(f"fixed spacing in {len(changed)} file(s)" + "".join(f"\n  {label}" for label in changed))

    return 0

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.path.resolve()

    if not root.is_dir():
        parser.error(f"{root} is not a directory")

    project = detect(root, args.exclude)

    if args.fix_spacing:
        return run_spacing_fix(project)

    rules = [rule for rule in all_rules() if not args.only or rule.id.startswith(tuple(args.only))]
    results = report.run(project, rules)
    print_results(args, project, results)

    below_minimum = args.min_score is not None and report.overall_score(results) < args.min_score

    return 1 if below_minimum else 0
