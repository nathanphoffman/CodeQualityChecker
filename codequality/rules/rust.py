
from ..models import Project, Result
from ..registry import rule

# --- core Rust ---------------------------------------------------------------

@rule("RUST-001", "Cargo.lock is committed for binaries", language="rust", severity="info")
def cargo_lock(p: Project) -> Result:
    return Result.passed() if (p.root / "Cargo.lock").exists() else Result.failed("no Cargo.lock")


@rule("RUST-002", "rustfmt / clippy configured", language="rust", severity="warn", checkable="partial")
def fmt_clippy(p: Project) -> Result:
    found = sum((p.root / n).exists() for n in ("rustfmt.toml", ".rustfmt.toml", "clippy.toml", ".clippy.toml"))
    return Result.scored(found / 2, f"{found}/2 config files found")


@rule("RUST-003", "Few unwrap()/expect() calls in non-test code", language="rust", severity="warn")
def unwrap_usage(p: Project) -> Result:
    files = [f for f in p.files(".rs") if "tests" not in f.parts]
    if not files:
        return Result.passed("no source files")
    hits = 0
    for f in files:
        text = f.read_text(errors="ignore")
        hits += text.count(".unwrap(") + text.count(".expect(")
    per_file = hits / len(files)
    return Result.scored(1 - per_file / 5, f"{hits} calls across {len(files)} files")


# --- frameworks (add rules per framework here) --------------------------------

@rule("RUST-AXUM-001", "axum: placeholder", language="rust", framework="axum", checkable="manual")
def axum_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("RUST-ACTIX-001", "actix: placeholder", language="rust", framework="actix", checkable="manual")
def actix_placeholder(p: Project) -> Result:
    return Result.manual()


@rule("RUST-TAURI-001", "tauri: placeholder", language="rust", framework="tauri", checkable="manual")
def tauri_placeholder(p: Project) -> Result:
    return Result.manual()
