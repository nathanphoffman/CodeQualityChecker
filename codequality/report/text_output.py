import sys

from ..models import Status
from .grouping import PERCENT, group_results, letter, overall_score

# ANSI styles, left empty when output is piped or redirected so files stay clean.
USE_COLOR = sys.stdout.isatty()
GREEN, YELLOW, RED, BOLD, DIM, RESET = ("\033[" + code + "m" if USE_COLOR else "" for code in ("32", "33", "31", "1", "2", "0"))
WIDTH = 78
GOOD_SCORE, OK_SCORE = 90, 70
HEAVY_LINE = "━" * WIDTH
BOX_INNER_WIDTH = WIDTH - 2


def score_color(score):
    """Green for an A, yellow for a C or better, red below that. `score` is 0-100."""
    if score >= GOOD_SCORE:
        return GREEN
    return YELLOW if score >= OK_SCORE else RED


def print_banner(left, right, score):
    """A heading between two heavy lines, with the text on the left and the score on the right."""
    gap = WIDTH - len(left) - len(right) - 2
    print(f"{BOLD}{score_color(score)}{HEAVY_LINE}\n {left}{' ' * gap}{right} \n{HEAVY_LINE}{RESET}")


def print_total(score):
    """The most important line: a double-line box with arrows pointing at the score."""
    text = f"▶▶▶   TOTAL SCORE   {score:.1f} / 100   {letter(score)}   ◀◀◀".center(BOX_INNER_WIDTH)
    print(f"{BOLD}{score_color(score)}╔{'═' * BOX_INNER_WIDTH}╗\n║{text}║\n╚{'═' * BOX_INNER_WIDTH}╝{RESET}\n")


def print_check(rule, result):
    """One sub-rule: small and dim, so the headings stand out."""
    mark = f"{result.score:.0%}" if result.status not in (Status.MANUAL, Status.SKIPPED) else result.status.value
    print(f"{DIM}    {result.status.value.upper():8}{rule.id}  {rule.title}  ({mark}){RESET}")
    if result.message:
        print(f"{DIM}            {result.message}{RESET}")


def print_group(group):
    if group.score is None:
        print_banner(group.title.upper(), "needs human review", 0)
    else:
        percent = group.score * PERCENT
        print_banner(group.title.upper(), f"{percent:.0f}%  {letter(percent)}", percent)
    for rule, result in group.entries:
        print_check(rule, result)
    print()


def print_text(project, results):
    print(f"Project: {project.root}")
    print(f"Languages: {', '.join(sorted(project.languages)) or 'none detected'}")
    print(f"Frameworks: {', '.join(sorted(project.frameworks)) or 'none detected'}\n")
    score = overall_score(results)
    print_total(score)
    for group in group_results(results):
        print_group(group)
    print_total(score)
