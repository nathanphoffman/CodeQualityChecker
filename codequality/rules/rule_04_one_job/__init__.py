"""Rule 4: One job per function. Judged by what a function's statements share, how it is named, and its branching."""
from ...registry import rule
from ..rule_02_clear_names.shared.judge_names import WORD_PATTERN
from .shared.cohesion import count_job_groups
from .shared.find_bodies import bodies_in_project
from .shared.grading import grade_bodies
from .shared.limits import JOINING_WORDS, MAX_COMPLEXITY, MAX_JOB_GROUPS, MAX_NESTING, MIN_STATEMENTS_TO_CHECK

def has_separate_jobs(body):
    """True when the statements split into groups that share no local variables."""

    if len(body.statement_variables) < MIN_STATEMENTS_TO_CHECK:
        return False

    return count_job_groups(body.statement_variables) > MAX_JOB_GROUPS

def has_joining_word(body):
    words = {word.lower() for word in WORD_PATTERN.findall(body.name)}

    return bool(words & JOINING_WORDS)

def is_too_complex(body):
    return body.branch_count + 1 > MAX_COMPLEXITY

def is_too_nested(body):
    return body.max_nesting > MAX_NESTING

def has_flag_parameter(body):
    """True when a boolean parameter sits beside others. A lone one (`set_enabled(on)`) is a plain setter."""

    return body.boolean_parameters > 0 and body.parameter_count > 1

@rule("RULE-04-COHESION", "Statements in a function work on the same variables")
def check_cohesion(project):
    return grade_bodies(bodies_in_project(project), has_separate_jobs, "split into unrelated groups of statements")

@rule("RULE-04-NAMES", "Function names don't say \"and\", \"or\" or \"then\"")
def check_function_names(project):
    return grade_bodies(bodies_in_project(project), has_joining_word, "are named as if they do several things")

@rule("RULE-04-COMPLEXITY", "Functions have at most 6 paths through them")
def check_complexity(project):
    return grade_bodies(bodies_in_project(project), is_too_complex, "have too many branches")

@rule("RULE-04-NESTING", "Code is nested at most 3 levels deep")
def check_nesting(project):
    return grade_bodies(bodies_in_project(project), is_too_nested, "nest blocks more than 3 levels deep")

@rule("RULE-04-FLAG-PARAMETERS", "Functions don't take true/false flag parameters")
def check_flag_parameters(project):
    return grade_bodies(bodies_in_project(project), has_flag_parameter, "take a boolean flag, so they likely do two jobs")
