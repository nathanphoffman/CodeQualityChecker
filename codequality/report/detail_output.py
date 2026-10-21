from ..explanations import CHECK_EXPLANATIONS, GROUP_SUMMARIES, NO_EXPLANATION
from ..models import Status
from .grouping import PERCENT, group_results, letter, overall_score
from .text_output import BOLD, DIM, RESET, print_banner, print_total, print_project_header

INDENT = "    "
SCALE_HELP = (
    "HOW TO READ THIS REPORT\n"
    "Every check gets a score from 0% to 100%. A check's group (one numbered rule from RULES.md) scores the average of its checks,\n"
    "weighted by severity, and the total score is the average of the groups. Grades: A 90+, B 80+, C 70+, D 60+, F below.\n"
    "Checks marked 'manual' or 'skipped' are not scored. Only checks below 100% need work, and each one says how to improve it.\n"
    "The limits (like 6 per file) are targets, not exact demands. Going a little over costs a little, and the score only drops fast when\n"
    "you are far over. Aim to be as close as is reasonable, and don't contort the code to hit an exact number. 6 is the ideal, 7 or 8 is fine."
)

def percent_text(result):
    return result.status.value if result.status in (Status.MANUAL, Status.SKIPPED) else f"{result.score:.1%}"

def print_quick(project, results):
    """One line per numbered rule, then the total. No detail on where the problems are."""
    print_project_header(project)

    for group in group_results(results):
        score = "needs human review" if group.score is None else f"{group.score * PERCENT:5.1f}%  {letter(group.score * PERCENT)}"
        print(f"{group.title:40}{score}")

    print()
    print_total(overall_score(results))

def print_full_check(rule, result):
    what, fix = CHECK_EXPLANATIONS.get(rule.id, NO_EXPLANATION)
    print(f"{BOLD}  {rule.id}  {rule.title}  [{percent_text(result)}]{RESET}")
    print(f"{INDENT}What it checks: {what}")

    if result.status in (Status.PASS, Status.MANUAL):
        print()

        return

    print(f"{INDENT}Found: {result.message or 'nothing more specific was recorded'}")
    print(f"{INDENT}How to fix: {fix}\n")

def print_full_group(group):
    percent = None if group.score is None else group.score * PERCENT
    print_banner(group.title.upper(), "needs human review" if percent is None else f"{percent:.0f}%  {letter(percent)}", percent or 0)
    print(f"{DIM}{GROUP_SUMMARIES.get(group.key, '')}{RESET}\n")

    for rule, result in group.entries:
        print_full_check(rule, result)

def print_full(project, results):
    print_project_header(project)
    print(f"{DIM}{SCALE_HELP}{RESET}\n")
    score = overall_score(results)
    print_total(score)

    for group in group_results(results):
        print_full_group(group)

    print_total(score)
