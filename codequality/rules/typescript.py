import re

from ..models import Project, Result
from ..registry import rule

# --- core TypeScript ---------------------------------------------------------

@rule("TS-001", "tsconfig has strict mode on", language="typescript", severity="error")
def strict_mode(p: Project) -> Result:
    cfg = p.root / "tsconfig.json"
    if not cfg.exists():
        return Result.failed("no tsconfig.json")
    text = cfg.read_text(errors="ignore")
    # looks for "strict": true, allowing any whitespace around the colon
    return Result.passed() if re.search(r'"strict"\s*:\s*true', text) else Result.failed("strict is not true")


@rule("TS-002", "Few explicit `any` types", language="typescript", severity="warn")
def any_usage(p: Project) -> Result:
    files = p.files(".ts", ".tsx")
    if not files:
        return Result.passed("no source files")
    # counts `: any`, `as any` and `<any>`, the three ways to write an explicit any
    hits = sum(len(re.findall(r":\s*any\b|\bas any\b|<any>", f.read_text(errors="ignore"))) for f in files)
    return Result.scored(1 - (hits / len(files)) / 3, f"{hits} `any` uses across {len(files)} files")


@rule("TS-003", "Linter configured (eslint/biome)", language="typescript", severity="warn")
def linter(p: Project) -> Result:
    names = ("eslint.config.js", "eslint.config.mjs", "eslint.config.ts", ".eslintrc", ".eslintrc.json",
             ".eslintrc.js", "biome.json", "biome.jsonc")
    return Result.passed() if any((p.root / n).exists() for n in names) else Result.failed("no linter config")


# --- frameworks (add rules per framework here) --------------------------------

@rule("TS-REACT-001", "react: placeholder", language="typescript", framework="react", checkable="manual")
def react_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("TS-NEXT-001", "next: placeholder", language="typescript", framework="next", checkable="manual")
def next_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("TS-EXPRESS-001", "express: placeholder", language="typescript", framework="express", checkable="manual")
def express_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("TS-NEST-001", "nest: placeholder", language="typescript", framework="nest", checkable="manual")
def nest_placeholder(p: Project) -> Result:
    return Result.manual()
