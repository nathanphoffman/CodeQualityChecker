def count_job_groups(statement_variables):
    """Groups of statements that share local variables. Statements using no locals can't be tied to a job."""
    groups = []
    for variables in statement_variables:
        if not variables:
            continue
        touching = [group for group in groups if group & variables]
        untouched = [group for group in groups if not group & variables]
        groups = untouched + [set(variables).union(*touching)]
    return len(groups)
