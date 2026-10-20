import os
from pathlib import Path

from ....source_code import SUFFIX_LANGUAGE, read_source
from .find_functions import find_functions

def parse_source_files(project):
    """Maps each Rust/TypeScript/Deor file to the functions found in it (Deor macros count as functions)."""

    return {
        project.label_for(path): find_functions(read_source(path), SUFFIX_LANGUAGE[path.suffix])
        for path in project.files(*SUFFIX_LANGUAGE)
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
        subfolders[:] = [subfolder for subfolder in subfolders if not Path(folder, subfolder).name.startswith(".") and not project.is_ignored(Path(folder, subfolder))]
        counts[project.label_for(folder)] = len([name for name in subfolders + names if not name.startswith(".") and not project.is_ignored(Path(folder, name))])

    return counts
