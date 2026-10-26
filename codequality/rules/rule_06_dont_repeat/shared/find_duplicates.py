from ....source_code import items_in_project
from ..python.python_shapes import python_shapes
from ..tree_sitter.tree_shapes import tree_shapes
from .limits import MIN_DUPLICATE_STATEMENTS, MIN_SHAPE_SIZE

def shapes_in_project(project):
    """[(file label, Function_Shape)] for every function in non-test Python, Rust and TypeScript files."""

    return items_in_project(project, python_shapes, tree_shapes)

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
