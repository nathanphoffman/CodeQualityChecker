
from ..models import SEVERITY_INFO, SEVERITY_WARN, Project, Result
from ..registry import rule
from ..source_code import RUST, read_source

MAX_UNWRAPS_PER_FILE = 5  # this many unwrap()/expect() calls per file scores zero

# --- core Rust ---------------------------------------------------------------

@rule("RUST-001", "Cargo.lock is committed for binaries", language=RUST, severity=SEVERITY_INFO)
def cargo_lock(project: Project) -> Result:
    return Result.passed() if (project.root / "Cargo.lock").exists() else Result.failed("no Cargo.lock")

@rule("RUST-002", "rustfmt / clippy configured", language=RUST, severity=SEVERITY_WARN, checkable="partial")
def fmt_clippy(project: Project) -> Result:
    found = sum((project.root / name).exists() for name in ("rustfmt.toml", ".rustfmt.toml", "clippy.toml", ".clippy.toml"))

    return Result.scored(found / 2, f"{found}/2 config files found")

@rule("RUST-003", "Few unwrap()/expect() calls in non-test code", language=RUST, severity=SEVERITY_WARN)
def unwrap_usage(project: Project) -> Result:
    files = [source_file for source_file in project.files(".rs") if "tests" not in source_file.parts]

    if not files:
        return Result.passed("no source files")

    hits = 0

    for source_file in files:
        text = read_source(source_file)
        hits += text.count(".unwrap(") + text.count(".expect(")

    per_file = hits / len(files)

    return Result.scored(1 - per_file / MAX_UNWRAPS_PER_FILE, f"{hits} calls across {len(files)} files")
