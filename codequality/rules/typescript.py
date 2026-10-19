import re

from ..models import CHECK_MANUAL, Project, Result, SEVERITY_ERROR, SEVERITY_WARN
from ..registry import rule
from ..source_code import TSCONFIG_FILE, TYPESCRIPT, TYPESCRIPT_SUFFIXES, read_source

MAX_ANY_PER_FILE = 3  # this many explicit `any` types per file scores zero

# --- core TypeScript ---------------------------------------------------------

@rule("TS-001", "tsconfig has strict mode on", language=TYPESCRIPT, severity=SEVERITY_ERROR)
def strict_mode(p: Project) -> Result:
    cfg = p.root / TSCONFIG_FILE

    if not cfg.exists():
        return Result.failed("no tsconfig.json")

    text = read_source(cfg)

    # looks for "strict": true, allowing any whitespace around the colon
    return Result.passed() if re.search(r'"strict"\s*:\s*true', text) else Result.failed("strict is not true")

@rule("TS-002", "Few explicit `any` types", language=TYPESCRIPT, severity=SEVERITY_WARN)
def any_usage(p: Project) -> Result:
    files = p.files(*TYPESCRIPT_SUFFIXES)

    if not files:
        return Result.passed("no source files")

    # counts `: any`, `as any` and `<any>`, the three ways to write an explicit any
    hits = sum(len(re.findall(r":\s*any\b|\bas any\b|<any>", read_source(f))) for f in files)

    return Result.scored(1 - (hits / len(files)) / MAX_ANY_PER_FILE, f"{hits} `any` uses across {len(files)} files")

@rule("TS-003", "Linter configured (eslint/biome)", language=TYPESCRIPT, severity=SEVERITY_WARN)
def linter(p: Project) -> Result:
    names = ("eslint.config.js", "eslint.config.mjs", "eslint.config.ts", ".eslintrc", ".eslintrc.json",
             ".eslintrc.js", "biome.json", "biome.jsonc")

    return Result.passed() if any((p.root / n).exists() for n in names) else Result.failed("no linter config")

# --- frameworks (add rules per framework here) --------------------------------

@rule("TS-REACT-001", "react: placeholder", language=TYPESCRIPT, framework="react", checkable=CHECK_MANUAL)
def react_placeholder(p: Project) -> Result:
    return Result.manual()

@rule("TS-NEXT-001", "next: placeholder", language=TYPESCRIPT, framework="next", checkable=CHECK_MANUAL)
def next_placeholder(p: Project) -> Result:
    return Result.manual()

@rule("TS-EXPRESS-001", "express: placeholder", language=TYPESCRIPT, framework="express", checkable=CHECK_MANUAL)
def express_placeholder(p: Project) -> Result:
    return Result.manual()

@rule("TS-NEST-001", "nest: placeholder", language=TYPESCRIPT, framework="nest", checkable=CHECK_MANUAL)
def nest_placeholder(p: Project) -> Result:
    return Result.manual()
