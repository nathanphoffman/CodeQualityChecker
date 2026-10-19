"""Rule 1: Power of 6s. Everything should have 6 or fewer; functions aim for 6 lines, hard cap 36."""
from ...registry import rule
from .measure import functions_per_file, items_per_folder, per_function
from .scoring import function_length_credit, grade, strict_credit


@rule("RULE-01-FUNCTIONS-PER-FILE", "At most 6 functions per file")
def check_functions_per_file(project):
    return grade(functions_per_file(project), strict_credit, "files")


@rule("RULE-01-ARGUMENTS", "At most 6 arguments per function")
def check_arguments(project):
    return grade(per_function(project, "argument_count"), strict_credit, "functions")


@rule("RULE-01-FUNCTION-LENGTH", "Functions are 6 lines or fewer (hard cap 36)")
def check_function_length(project):
    return grade(per_function(project, "line_count"), function_length_credit, "functions")


@rule("RULE-01-FOLDER-ITEMS", "At most 6 items per folder")
def check_folder_items(project):
    return grade(items_per_folder(project), strict_credit, "folders")
