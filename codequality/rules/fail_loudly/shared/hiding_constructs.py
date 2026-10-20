from ....models import SEVERITY_WARN
from ...be_secure.shared.call_checks import ANY_NAME, Call_Check, Entry
from ...be_secure.shared.judge_uses import is_finding
from ...be_secure.shared.uses import uses_in_project

# Calls that throw errors or warnings away. The flags are written in two pieces so this file does not flag itself.
HIDING_CHECK = Call_Check("hiding", "Calls that hide errors", SEVERITY_WARN, {
    "python": (Entry("contextlib.suppress"), Entry("suppress"),
               Entry(ANY_NAME, ("errors=" + "'ignore'",)), Entry(ANY_NAME, ("errors=" + "'replace'",)),
               Entry("warnings.filterwarnings", ("'ig" + "nore'",)), Entry("warnings.simplefilter", ("'ig" + "nore'",)),
               Entry(ANY_NAME, ("check=" + "False",))),

    "typescript": (),
    "rust": (),
    "deor": (),
})

def hiding_constructs(project):
    """[(file label, line number)] for every call that hides errors."""
    found = []

    for label, language, uses in uses_in_project(project):
        found += [(label, use.line_number) for use in uses if is_finding(use, HIDING_CHECK, language)]

    return found
