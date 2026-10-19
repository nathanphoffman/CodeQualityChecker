
from ..models import CHECK_MANUAL, Project, Result, SEVERITY_INFO, SEVERITY_WARN
from ..registry import rule
from ..source_code import RUST, read_source

MAX_UNWRAPS_PER_FILE = 5  # this many unwrap()/expect() calls per file scores zero

# --- core Rust ---------------------------------------------------------------

@rule("RUST-001", "Cargo.lock is committed for binaries", language=RUST, severity=SEVERITY_INFO)
def cargo_lock(p: Project) -> Result:
    return Result.passed() if (p.root / "Cargo.lock").exists() else Result.failed("no Cargo.lock")


@rule("RUST-002", "rustfmt / clippy configured", language=RUST, severity=SEVERITY_WARN, checkable="partial")
def fmt_clippy(p: Project) -> Result:
    found = sum((p.root / n).exists() for n in ("rustfmt.toml", ".rustfmt.toml", "clippy.toml", ".clippy.toml"))
    return Result.scored(found / 2, f"{found}/2 config files found")


@rule("RUST-003", "Few unwrap()/expect() calls in non-test code", language=RUST, severity=SEVERITY_WARN)
def unwrap_usage(p: Project) -> Result:
    files = [f for f in p.files(".rs") if "tests" not in f.parts]
    if not files:
        return Result.passed("no source files")
    hits = 0
    for f in files:
        text = read_source(f)
        hits += text.count(".unwrap(") + text.count(".expect(")
    per_file = hits / len(files)
    return Result.scored(1 - per_file / MAX_UNWRAPS_PER_FILE, f"{hits} calls across {len(files)} files")


# --- frameworks (add rules per framework here) --------------------------------

@rule("RUST-AXUM-001", "axum: placeholder", language=RUST, framework="axum", checkable=CHECK_MANUAL)
def axum_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("RUST-ACTIX-001", "actix: placeholder", language=RUST, framework="actix", checkable=CHECK_MANUAL)
def actix_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("RUST-TAURI-001", "tauri: placeholder", language=RUST, framework="tauri", checkable=CHECK_MANUAL)
def tauri_placeholder(p: Project) -> Result:
    return Result.manual()
