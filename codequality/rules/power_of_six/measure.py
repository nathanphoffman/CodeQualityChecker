import os
from pathlib import Path

from ...source_code import FUNCTION_SUFFIX_LANGUAGE, read_source
from .find_functions import find_functions

def parse_source_files(project):
    """Maps each Rust/TypeScript/Deor file to the functions found in it (Deor macros count as functions)."""

    return {
        project.label_for(path): find_functions(read_source(path), FUNCTION_SUFFIX_LANGUAGE[path.suffix])
        for path in project.files(*FUNCTION_SUFFIX_LANGUAGE)
    }

def functions_per_file(project):
    return {file: len(infos) for file, infos in parse_source_files(project).items()}

def per_function(project, attribute):
    values = {}

    for file, infos in parse_source_files(project).items():
        for info in infos:
            values[f"{file}:{info.line_number} {info.name}"] = getattr(info, attribute)

    return values

def items_per_folder(project):
    counts = {}

    for folder, subfolders, names in os.walk(project.root):
        subfolders[:] = [s for s in subfolders if not Path(folder, s).name.startswith(".") and not project.is_ignored(Path(folder, s))]
        counts[project.label_for(folder)] = len([n for n in subfolders + names if not n.startswith(".") and not project.is_ignored(Path(folder, n))])

    return counts
