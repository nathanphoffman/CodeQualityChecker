import json

from ..report.grouping import letter, rounded_score, shown_percent
from ..report.text_output import BOLD, DIM, GREEN, RED, RESET, print_total
from .differences import NO_CHANGE, check_changes, group_changes, overall_change, percent

def arrow(old, new) -> str:
    """'94.9% → 95.1%', with 'new' or 'gone' when one side does not exist."""

    if old is None:
        return f"new → {shown_percent(new, 1)}%"

    return f"{shown_percent(old, 1)}% → gone" if new is None else f"{shown_percent(old, 1)}% → {shown_percent(new, 1)}%"

def signed(difference) -> str:
    return f"{difference:+.1f}"

def color_for(difference) -> str:
    """Green for better, red for worse, nothing for no change."""

    if abs(difference) <= NO_CHANGE * 100:
        return ""

    return GREEN if difference > 0 else RED

def print_change_line(label, change, scale) -> None:
    old, new = percent(change.old), percent(change.new)
    difference = change.difference * scale
    shown = f"  {signed(difference)}" if change.old is not None and change.new is not None else ""
    print(f"{color_for(difference)}    {label:34}{arrow(old, new)}{shown}{RESET}")

def print_comparison(ref, short, old_results, new_results) -> None:
    """The overall score then and now, the groups that moved, and the checks that moved (worst first)."""
    old, new = overall_change(old_results, new_results)
    print(f"{BOLD}Compared with {ref} ({short}). 'Now' is the files as they are on disk, uncommitted changes included.{RESET}\n")
    print(f"Then: {shown_percent(old, 1)}  {letter(old)}")
    print(f"Now:  {shown_percent(new, 1)}  {letter(new)}   {color_for(new - old)}{signed(new - old)}{RESET}\n")
    print_total(new)
    every_group = group_changes(old_results, new_results)
    moved_groups = [change for change in every_group if change.moved]
    print(f"{BOLD}Groups that changed (worst first){RESET}")

    for change in moved_groups:
        print_change_line(change.title, change, 100)

    print(f"{DIM}    {len(every_group) - len(moved_groups)} groups unchanged{RESET}\n")
    print(f"{BOLD}Checks that changed (worst first){RESET}")

    for change in check_changes(old_results, new_results):
        print_change_line(change.id, change, 100)

    print()

def comparison_to_json(ref, short, old_results, new_results) -> str:
    old, new = overall_change(old_results, new_results)
    checks = [{"id": change.id, "title": change.title, "old": change.old, "new": change.new} for change in check_changes(old_results, new_results)]

    return json.dumps({"compared_with": ref, "commit": short, "old_score": rounded_score(old, 1), "new_score": rounded_score(new, 1),
                       "difference": round(new - old, 1), "changed_checks": checks}, indent=2)
