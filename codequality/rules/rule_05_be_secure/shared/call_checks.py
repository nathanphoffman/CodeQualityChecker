"""The calls and constructs rule 5 looks for, as data. One Call_Check becomes one scored rule."""
from typing import NamedTuple

from .limits import INPUT_WORDS, SECRET_WORDS

ANY_NAME = "*"  # an Entry with this name matches any call, judged only by its text

class Entry(NamedTuple):
    """A bare name like "eval" must match exactly. A dotted name like "os.system" also matches "x.os.system"."""
    name: str
    must_contain: tuple = ()  # every one of these must be in the use's text
    must_not_contain: tuple = ()
    prefix: str = ""  # the use's text must start with this

class Call_Check(NamedTuple):
    id: str
    title: str
    severity: str
    entries: dict  # language -> tuple of Entry
    names_words: tuple = ()  # if given, a variable name used inside must contain one of these

    line_words: tuple = ()  # if given, the source line must contain one of these

def shell_calls(prefix, names):
    return tuple(Entry(f"{prefix}.{name}", ("shell=True",)) for name in names)

def hash_calls(names, algorithms):
    entries = []

    for name in names:
        for algorithm in algorithms:
            entries += [Entry(name, (quote + algorithm + quote,)) for quote in ("'", '"')]

    return tuple(entries)

def log_calls(receivers, methods):
    entries = []

    for receiver in receivers:
        entries += [Entry(f"{receiver}.{method}") for method in methods]

    return tuple(entries)

SQL_METHODS = (
    # A SELECT also needs "*", a column list or a WHERE, so a sentence like "Select an item from the list" passes.
    Entry("dynamic_string", ("* FROM",), prefix="SELECT "),
    Entry("dynamic_string", (" FROM ", " WHERE "), prefix="SELECT "),
    Entry("dynamic_string", (", ", " FROM "), prefix="SELECT "),
    Entry("dynamic_string", ("COUNT(", " FROM"), prefix="SELECT "),

    Entry("dynamic_string", prefix="INSERT INTO "),
    Entry("dynamic_string", (" SET ",), prefix="UPDATE "),
    Entry("dynamic_string", prefix="DELETE FROM "),
)

LOG_METHODS = ("debug", "info", "warning", "warn", "error", "exception", "critical", "log")
PYTHON_LOGGERS = ("logging", "logger", "log")
SHELLS = ('"sh"', '"bash"', '"zsh"', '"cmd"', '"powershell"')

# Keyword flags like verify=False are written in two pieces so this file does not flag itself.
CALL_CHECKS = [
    Call_Check("RULE-05-SQL-STRINGS", "SQL is not built by joining strings", "error", {
        "python": SQL_METHODS, "rust": SQL_METHODS, "typescript": SQL_METHODS, "hare": SQL_METHODS,
    }),

    Call_Check("RULE-05-RUN-STRINGS", "No eval or shell commands built from strings", "error", {
        "python": (Entry("eval"), Entry("exec"), Entry("os.system"), Entry("os.popen"))
        + shell_calls("subprocess", ("run", "call", "check_call", "check_output", "Popen")),
        "typescript": (Entry("eval"), Entry("Function"), Entry("exec"), Entry("child_process.exec"), Entry("child_process.execSync"),
                       Entry("execSync"), Entry("vm.runInNewContext"), Entry("vm.runInThisContext"),
                       Entry("spawn", ("shell:true",)), Entry("spawnSync", ("shell:true",)), Entry("child_process.spawn", ("shell:true",))),

        "rust": (Entry("libc.system"),) + tuple(Entry("Command.new", (shell,)) for shell in SHELLS),
        "hare": tuple(Entry(f"exec.{name}", (shell,)) for name in ("cmd", "cmdv") for shell in SHELLS),
    }),

    Call_Check("RULE-05-UNSAFE-LOADING", "No loading of untrusted data that can run code", "error", {
        "python": (Entry("pickle.load"), Entry("pickle.loads"), Entry("cPickle.loads"), Entry("marshal.load"),
                   Entry("marshal.loads"), Entry("shelve.open"), Entry("dill.loads"), Entry("jsonpickle.decode"),
                   Entry("yaml.unsafe_load"), Entry("yaml.load", must_not_contain=("SafeLoader",))),
        "typescript": (Entry("unserialize"),),

        "rust": (),
        "hare": (),
    }),

    Call_Check("RULE-05-WEAK-HASH", "No MD5 or SHA1 hashing", "warn", {
        "python": (Entry("hashlib.md5"), Entry("hashlib.sha1")) + hash_calls(("hashlib.new",), ("md5", "sha1")),
        "typescript": hash_calls(("createHash", "crypto.createHash"), ("md5", "sha1")),
        "rust": (Entry("Md5.new"), Entry("md5.compute"), Entry("Sha1.new"), Entry("Sha1.digest")),
        "hare": (Entry("md5.md5"), Entry("sha1.sha1")),
    }),

    Call_Check("RULE-05-WEAK-RANDOM", "Secrets are not made with ordinary random numbers", "warn", {
        "python": tuple(Entry(f"random.{name}") for name in ("random", "randint", "choice", "choices", "randrange", "getrandbits")),
        "typescript": (Entry("Math.random"),),
        "rust": (Entry("rand.random"), Entry("rand.thread_rng"), Entry("thread_rng")),
        "hare": tuple(Entry(f"random.{name}") for name in ("init", "u32", "u64", "u32n", "u64n")),
    }, line_words=SECRET_WORDS),

    Call_Check("RULE-05-SAFETY-OFF", "No turned-off certificate checks or left-on debug mode", "error", {
        "python": (Entry(ANY_NAME, ("verify=" + "False",)), Entry(ANY_NAME, ("check_hostname=" + "False",)),
                   Entry(ANY_NAME, ("autoescape=" + "False",)), Entry(ANY_NAME, ("debug=" + "True",)),
                   Entry("ssl._create_unverified_context")),
        "typescript": (Entry(ANY_NAME, ("rejectUnauthorized:false",)), Entry("assign.NODE_TLS_REJECT_UNAUTHORIZED")),

        "rust": (Entry(ANY_NAME, ("danger_accept_invalid_certs(true)",)),
                 Entry(ANY_NAME, ("danger_accept_invalid_hostnames(true)",))),
        "hare": (),
    }),

    Call_Check("RULE-05-RISKY-OUTPUT", "Little output that skips escaping, and little unsafe", "info", {
        "python": (Entry("mark_safe"), Entry("Markup"), Entry("markupsafe.Markup")),
        "typescript": (Entry("document.write"), Entry("assign.innerHTML"), Entry("assign.outerHTML"),
                       Entry("jsx.dangerouslySetInnerHTML"), Entry(ANY_NAME, (".insertAdjacentHTML(",))),
        "rust": (Entry("unsafe"),),
        "hare": (),
    }),

    Call_Check("RULE-05-USER-PATHS", "File paths are not built from user input", "info", {
        "python": tuple(Entry(name) for name in ("os.path.join", "Path", "pathlib.Path", "open", "send_file", "send_from_directory")),
        "typescript": tuple(Entry(f"fs.{name}") for name in ("readFile", "readFileSync", "writeFile", "createReadStream"))
        + (Entry("path.join"), Entry("path.resolve"), Entry("res.sendFile")),

        "rust": (Entry("Path.new"), Entry("PathBuf.from"), Entry("File.open"), Entry("File.create"),
                 Entry("fs.read_to_string"), Entry("fs.read")),
        "hare": tuple(Entry(f"os.{name}") for name in ("open", "create", "mkdir", "remove", "rename")),
    }, names_words=INPUT_WORDS),

    Call_Check("RULE-05-SECRET-LOGGING", "Secrets are not printed or logged", "info", {
        "python": (Entry("print"),) + log_calls(PYTHON_LOGGERS, LOG_METHODS),
        "typescript": log_calls(("console", "logger"), LOG_METHODS),
        "rust": tuple(Entry(name) for name in ("println", "eprintln", "print", "eprint", "dbg", "info", "warn", "error", "debug", "trace")),
        "hare": tuple(Entry(f"fmt.{name}") for name in ("print", "println", "printf", "printfln", "error", "errorln", "errorf", "errorfln")),
    }, names_words=SECRET_WORDS),
]

# Deor code is judged by its standard library's functions, and its `rust` blocks by the Rust entries.
DEOR_ENTRIES = {
    "RULE-05-WEAK-RANDOM": tuple(Entry(name) for name in ("m_rand_int", "m_rand_float", "m_rand_bool")),
    "RULE-05-USER-PATHS": tuple(Entry(name) for name in ("f_read", "f_write", "f_append", "f_exists", "f_lines", "f_delete")),
    "RULE-05-SECRET-LOGGING": (Entry("print"),),
}

for check in CALL_CHECKS:
    check.entries["deor"] = check.entries["rust"] + DEOR_ENTRIES.get(check.id, ())
