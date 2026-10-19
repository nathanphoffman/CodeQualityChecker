from ...source_code import SUFFIX_LANGUAGE, non_test_files
from .limits import MIN_DUPLICATE_STATEMENTS, MIN_SHAPE_SIZE
from .python_shapes import python_shapes
from .tree_shapes import tree_shapes


def shapes_in_project(project):
    """[(file label, Function_Shape)] for every function in non-test Python, Rust and TypeScript files."""
    found = []
    for path in non_test_files(project, SUFFIX_LANGUAGE):
        language = SUFFIX_LANGUAGE[path.suffix]
        source = path.read_text(errors="ignore")
        shapes = python_shapes(source) if language == "python" else tree_shapes(source, language)
        found += [(project.label_for(path), shape) for shape in shapes]
    return found


def repeated_functions(entries):
    """Functions whose whole body matches an earlier function: [(copy entry, original entry)]."""
    first_seen, copies = {}, []
    for entry in sorted(entries, key=lambda entry: (entry[0], entry[1].line_number)):
        body = tuple(statement.shape for statement in entry[1].sequences[0])
        big_enough = sum(statement.size for statement in entry[1].sequences[0]) >= MIN_SHAPE_SIZE
        if big_enough and body in first_seen:
            copies.append((entry, first_seen[body]))
        elif big_enough:
            first_seen[body] = entry
    return copies


def repeated_blocks(entries):
    """Runs of statements matching an earlier run: [(label, copy statements, original label, original statements)]."""
    first_seen, repeats = {}, []
    for label, function in sorted(entries, key=lambda entry: (entry[0], entry[1].line_number)):
        for sequence in function.sequences:
            for start in range(len(sequence) - MIN_DUPLICATE_STATEMENTS + 1):
                run = sequence[start:start + MIN_DUPLICATE_STATEMENTS]
                key = tuple(statement.shape for statement in run)
                if sum(statement.size for statement in run) < MIN_SHAPE_SIZE:
                    continue
                if key in first_seen:
                    repeats.append((label, run, *first_seen[key]))
                else:
                    first_seen[key] = (label, run)
    return repeats
