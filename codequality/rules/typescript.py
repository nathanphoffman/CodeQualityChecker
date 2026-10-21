import re

from ..models import CHECK_MANUAL, Project, Result, SEVERITY_ERROR, SEVERITY_INFO, SEVERITY_WARN
from ..registry import rule
from ..source_code import TSCONFIG_FILE, TYPESCRIPT, TYPESCRIPT_SUFFIXES, non_test_files, read_source

MAX_ANY_PER_FILE = 3  # this many explicit `any` types per file scores zero

# Clever on purpose: a NEXT_PUBLIC_ variable whose name says it holds something private.
#   NEXT_PUBLIC_, any other name characters, then a secret-sounding word (case-insensitive, so env names and code both match)
NEXT_PUBLIC_SECRET = re.compile(r"NEXT_PUBLIC_\w*(?:SECRET|PASSWORD|PRIVATE|TOKEN)", re.I)

# Clever on purpose: `<img ` and `<a href="/...` (a plain internal link) against `<Image ` and `<Link `.
PLAIN_IMAGE_OR_LINK = re.compile(r"<img\b|<a\s[^>]*href=[\"']/")

# the start of an <Image or <Link tag; \b stops it matching longer names like <ImageGallery
NEXT_IMAGE_OR_LINK = re.compile(r"<Image\b|<Link\b")

# --- core TypeScript ---------------------------------------------------------

@rule("TS-001", "tsconfig has strict mode on", language=TYPESCRIPT, severity=SEVERITY_ERROR)
def strict_mode(project: Project) -> Result:
    config_path = project.root / TSCONFIG_FILE

    if not config_path.exists():
        return Result.failed("no tsconfig.json")

    text = read_source(config_path)

    # looks for "strict": true, allowing any whitespace around the colon
    return Result.passed() if re.search(r'"strict"\s*:\s*true', text) else Result.failed("strict is not true")

@rule("TS-002", "Few explicit `any` types", language=TYPESCRIPT, severity=SEVERITY_WARN)
def any_usage(project: Project) -> Result:
    files = project.files(*TYPESCRIPT_SUFFIXES)

    if not files:
        return Result.passed("no source files")

    # counts `: any`, `as any` and `<any>`, the three ways to write an explicit any
    hits = sum(len(re.findall(r":\s*any\b|\bas any\b|<any>", read_source(source_file))) for source_file in files)

    return Result.scored(1 - (hits / len(files)) / MAX_ANY_PER_FILE, f"{hits} `any` uses across {len(files)} files")

@rule("TS-003", "Linter configured (eslint/biome)", language=TYPESCRIPT, severity=SEVERITY_WARN)
def linter(project: Project) -> Result:
    names = ("eslint.config.js", "eslint.config.mjs", "eslint.config.ts", ".eslintrc", ".eslintrc.json",
             ".eslintrc.js", "biome.json", "biome.jsonc")

    return Result.passed() if any((project.root / name).exists() for name in names) else Result.failed("no linter config")

# --- frameworks (add rules per framework here) --------------------------------

@rule("TS-REACT-001", "react: placeholder", language=TYPESCRIPT, framework="react", checkable=CHECK_MANUAL)
def react_placeholder(project: Project) -> Result:
    return Result.manual()

@rule("TS-NEXT-001", "next: no secrets in NEXT_PUBLIC_ variables", language=TYPESCRIPT, framework="next", severity=SEVERITY_WARN)
def next_public_secrets(project: Project) -> Result:
    paths = non_test_files(project, TYPESCRIPT_SUFFIXES) + sorted(project.root.glob(".env*"))
    hits = [project.label_for(path) for path in paths if NEXT_PUBLIC_SECRET.search(read_source(path))]

    # NEXT_PUBLIC_ values are shipped to every visitor's browser, so a real secret there is public
    return Result.failed(f"browser-visible secret names in: {', '.join(hits)}") if hits else Result.passed()

@rule("TS-NEXT-002", "next: use next/image and next/link", language=TYPESCRIPT, framework="next", severity=SEVERITY_INFO)
def next_components(project: Project) -> Result:
    text = "\n".join(read_source(path) for path in non_test_files(project, TYPESCRIPT_SUFFIXES))
    plain, better = len(PLAIN_IMAGE_OR_LINK.findall(text)), len(NEXT_IMAGE_OR_LINK.findall(text))

    if not plain + better:
        return Result.passed("no images or links found")

    return Result.scored(better / (plain + better), f"{plain} plain <img>/<a> where next/image or next/link fits")

@rule("TS-EXPRESS-001", "express: placeholder", language=TYPESCRIPT, framework="express", checkable=CHECK_MANUAL)
def express_placeholder(project: Project) -> Result:
    return Result.manual()

@rule("TS-NEST-001", "nest: placeholder", language=TYPESCRIPT, framework="nest", checkable=CHECK_MANUAL)
def nest_placeholder(project: Project) -> Result:
    return Result.manual()
