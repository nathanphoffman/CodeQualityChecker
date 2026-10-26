from __future__ import annotations

import argparse
from pathlib import Path

from . import report
from .compare import Compare_Error, comparison_to_json, overall_change, print_comparison, project_at_ref, short_ref
from .detect import detect
from .fix_spacing import fix_spacing
from .registry import all_rules
from .report.grouping import rounded_score

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codequality", description="Grade a project against RULES.md")
    parser.add_argument("path", type=Path, nargs="?", default=Path("."), help="project root to check (default: current directory)")
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--only", action="append", default=[], help="only run rules whose ID starts with this, e.g. RULE-03 (repeatable)")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATTERN", help="skip files and folders whose name or relative path matches this wildcard, e.g. '*out.rs*' (repeatable)")
    parser.add_argument("--fix-spacing", action="store_true", help="add the missing blank lines and remove doubled ones (RULE-14) in place, then exit")
    parser.add_argument("--compare", metavar="REF", help="grade the project as it was at this git commit, branch or tag and show what got better or worse since (instead of the normal report)")
    parser.add_argument("--fail-if-worse", action="store_true", help="with --compare: exit 1 if the overall score is lower than it was at REF")
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

def run_comparison(args, project, rules) -> int:
    """Grades the project now and at args.compare, prints the differences, and returns the exit code the flags ask for."""

    try:
        short = short_ref(project.root, args.compare)

        with project_at_ref(project.root, args.compare) as old_root:
            old_results = report.run(detect(old_root, args.exclude), rules)
    except Compare_Error as error:
        raise SystemExit(f"codequality: cannot compare with {args.compare}: {error}") from error

    new_results = report.run(project, rules)
    old_score, new_score = overall_change(old_results, new_results)

    if args.json:
        print(comparison_to_json(args.compare, short, old_results, new_results))
    else:
        print_comparison(args.compare, short, old_results, new_results)

    got_worse = args.fail_if_worse and rounded_score(new_score, 1) < rounded_score(old_score, 1)
    below_minimum = args.min_score is not None and new_score < args.min_score

    return 1 if got_worse or below_minimum else 0

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.path.resolve()

    if args.fail_if_worse and not args.compare:
        parser.error("--fail-if-worse only works together with --compare")

    if not root.is_dir():
        parser.error(f"{root} is not a directory")

    project = detect(root, args.exclude)

    if args.fix_spacing:
        return run_spacing_fix(project)

    rules = [rule for rule in all_rules() if not args.only or rule.id.startswith(tuple(args.only))]

    if args.compare:
        return run_comparison(args, project, rules)

    results = report.run(project, rules)
    print_results(args, project, results)

    below_minimum = args.min_score is not None and report.overall_score(results) < args.min_score

    return 1 if below_minimum else 0
