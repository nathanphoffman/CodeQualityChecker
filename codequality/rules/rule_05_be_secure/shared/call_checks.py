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

def any_call_with(*texts):
    """Entries that match any call whose text holds one of these pieces."""

    return tuple(Entry(ANY_NAME, (text,)) for text in texts)

def mode_calls(names, modes):
    """Every name paired with every file permission, like chmod with 0o777 and chmod with 0o666."""

    # two loops: each name gets its own entry for each mode, because an entry's must_contain parts all have to match
    return tuple(Entry(name, (mode,)) for name in names for mode in modes)

LOG_METHODS = ("debug", "info", "warning", "warn", "error", "exception", "critical", "log")
PYTHON_LOGGERS = ("logging", "logger", "log")
SHELLS = ('"sh"', '"bash"', '"zsh"', '"cmd"', '"powershell"')

WIDE_OPEN_PYTHON = ("511", "438")  # 0o777 and 0o666, which is how Python prints them back
WIDE_OPEN_C = ("0777", "0666")
CORS_HEADER = "Access-Control-Allow-Origin"
BROKEN_NODE_CIPHERS = ("-ecb", "'des", '"des', "rc4", "rc2")  # as written inside createCipheriv("aes-128-ecb", ...)

# Keyword flags like verify=False are written in two pieces so this file does not flag itself.
CALL_CHECKS = [
    Call_Check("RULE-05-SQL-STRINGS", "SQL is not built by joining strings", "error", {
        "python": SQL_METHODS, "rust": SQL_METHODS, "typescript": SQL_METHODS, "hare": SQL_METHODS,
        "c": SQL_METHODS, "go": SQL_METHODS, "fortran": SQL_METHODS, "csharp": SQL_METHODS, "rexx": SQL_METHODS,
    }),

    Call_Check("RULE-05-RUN-STRINGS", "No eval or shell commands built from strings", "error", {
        "python": (Entry("eval"), Entry("exec"), Entry("os.system"), Entry("os.popen"))
        + shell_calls("subprocess", ("run", "call", "check_call", "check_output", "Popen")),
        "typescript": (Entry("eval"), Entry("Function"), Entry("exec"), Entry("child_process.exec"), Entry("child_process.execSync"),
                       Entry("execSync"), Entry("vm.runInNewContext"), Entry("vm.runInThisContext"),
                       Entry("spawn", ("shell:true",)), Entry("spawnSync", ("shell:true",)), Entry("child_process.spawn", ("shell:true",))),

        "rust": (Entry("libc.system"),) + tuple(Entry("Command.new", (shell,)) for shell in SHELLS),
        "hare": tuple(Entry(f"exec.{name}", (shell,)) for name in ("cmd", "cmdv") for shell in SHELLS),  # every command function paired with every shell name
        "c": (Entry("system"), Entry("popen")),
        "fortran": (Entry("execute_command_line"), Entry("system")),
        "rexx": (Entry("interpret"), Entry("command")),  # `command` is a line sent to the operating system with a variable in it
        "csharp": (Entry("CSharpScript.EvaluateAsync"), Entry("CSharpScript.RunAsync"), Entry("Process.Start", ('"cmd"',)))
        + tuple(Entry(name, (shell,)) for name in ("ProcessStartInfo", "Process.Start") for shell in SHELLS),  # every process-starting name paired with every shell name
        "go": tuple(Entry(f"exec.{name}", (shell,)) for name in ("Command", "CommandContext") for shell in SHELLS),  # both functions with every shell name
    }),

    Call_Check("RULE-05-UNSAFE-LOADING", "No loading of untrusted data that can run code", "error", {
        "python": (Entry("pickle.load"), Entry("pickle.loads"), Entry("cPickle.loads"), Entry("marshal.load"),
                   Entry("marshal.loads"), Entry("shelve.open"), Entry("dill.loads"), Entry("jsonpickle.decode"),
                   Entry("yaml.unsafe_load"), Entry("yaml.load", must_not_contain=("SafeLoader",))),
        "typescript": (Entry("unserialize"),),

        "rust": (),
        "hare": (),
        "c": (),
        "go": (),
        "csharp": tuple(Entry(name) for name in ("BinaryFormatter", "NetDataContractSerializer", "SoapFormatter", "LosFormatter", "ObjectStateFormatter")),
    }),

    Call_Check("RULE-05-WEAK-HASH", "No MD5 or SHA1 hashing", "warn", {
        "python": (Entry("hashlib.md5"), Entry("hashlib.sha1")) + hash_calls(("hashlib.new",), ("md5", "sha1")),
        "typescript": hash_calls(("createHash", "crypto.createHash"), ("md5", "sha1")),
        "rust": (Entry("Md5.new"), Entry("md5.compute"), Entry("Sha1.new"), Entry("Sha1.digest")),
        "hare": (Entry("md5.md5"), Entry("sha1.sha1")),
        "c": tuple(Entry(name) for name in ("MD5", "MD5_Init", "SHA1", "SHA1_Init", "EVP_md5", "EVP_sha1")),
        "go": (Entry("md5.New"), Entry("md5.Sum"), Entry("sha1.New"), Entry("sha1.Sum")),
        "csharp": tuple(Entry(name) for name in ("MD5.Create", "MD5.HashData", "SHA1.Create", "SHA1.HashData", "MD5CryptoServiceProvider",
                                                "SHA1CryptoServiceProvider", "SHA1Managed")),
    }),

    Call_Check("RULE-05-WEAK-RANDOM", "Secrets are not made with ordinary random numbers", "warn", {
        "python": tuple(Entry(f"random.{name}") for name in ("random", "randint", "choice", "choices", "randrange", "getrandbits")),
        "typescript": (Entry("Math.random"),),
        "rust": (Entry("rand.random"), Entry("rand.thread_rng"), Entry("thread_rng")),
        "hare": tuple(Entry(f"random.{name}") for name in ("init", "u32", "u64", "u32n", "u64n")),
        "c": tuple(Entry(name) for name in ("rand", "srand", "random", "srandom", "drand48")),
        "fortran": (Entry("random_number"), Entry("random_seed")),
        "rexx": (Entry("random"),),
        "go": tuple(Entry(f"rand.{name}") for name in ("Int", "Intn", "Int63", "Int31", "Float64", "Seed")),
        "csharp": (Entry("Random"), Entry("Random.Shared.Next"), Entry("Random.Shared.NextBytes")),
    }, line_words=SECRET_WORDS),

    Call_Check("RULE-05-SAFETY-OFF", "No turned-off certificate checks or left-on debug mode", "error", {
        "python": (Entry(ANY_NAME, ("verify=" + "False",)), Entry(ANY_NAME, ("check_hostname=" + "False",)),
                   Entry(ANY_NAME, ("autoescape=" + "False",)), Entry(ANY_NAME, ("debug=" + "True",)),
                   Entry("ssl._create_unverified_context")),
        "typescript": (Entry(ANY_NAME, ("rejectUnauthorized:false",)), Entry("assign.NODE_TLS_REJECT_UNAUTHORIZED")),

        "rust": (Entry(ANY_NAME, ("danger_accept_invalid_certs(true)",)),
                 Entry(ANY_NAME, ("danger_accept_invalid_hostnames(true)",))),
        "hare": (),
        "c": (Entry("curl_easy_setopt", ("CURLOPT_SSL_VERIFYPEER,0",)), Entry("SSL_CTX_set_verify", ("SSL_VERIFY_NONE",))),
        "go": (),
        "csharp": (Entry("HttpClientHandler", ("ServerCertificateCustomValidationCallback",)),
                   Entry("HttpClientHandler", ("DangerousAcceptAnyServerCertificateValidator",)), Entry("UseDeveloperExceptionPage")),
    }),

    Call_Check("RULE-05-RISKY-OUTPUT", "Little output that skips escaping, and little unsafe", "info", {
        "python": (Entry("mark_safe"), Entry("Markup"), Entry("markupsafe.Markup")),
        "typescript": (Entry("document.write"), Entry("assign.innerHTML"), Entry("assign.outerHTML"),
                       Entry("jsx.dangerouslySetInnerHTML"), Entry(ANY_NAME, (".insertAdjacentHTML(",))),
        "rust": (Entry("unsafe"),),
        "hare": (),
        "c": tuple(Entry(name) for name in ("gets", "strcpy", "strcat", "sprintf", "vsprintf")),
        "fortran": (Entry("transfer"), Entry("c_loc"), Entry("c_f_pointer")),
        "go": (Entry("unsafe.Pointer"), Entry("template.HTML"), Entry("template.JS")),
        "csharp": (Entry("unsafe"), Entry("Html.Raw"), Entry("HtmlString"), Entry("MarkupString")),
    }),

    Call_Check("RULE-05-USER-PATHS", "File paths are not built from user input", "info", {
        "python": tuple(Entry(name) for name in ("os.path.join", "Path", "pathlib.Path", "open", "send_file", "send_from_directory")),
        "typescript": tuple(Entry(f"fs.{name}") for name in ("readFile", "readFileSync", "writeFile", "createReadStream"))
        + (Entry("path.join"), Entry("path.resolve"), Entry("res.sendFile")),

        "rust": (Entry("Path.new"), Entry("PathBuf.from"), Entry("File.open"), Entry("File.create"),
                 Entry("fs.read_to_string"), Entry("fs.read")),
        "hare": tuple(Entry(f"os.{name}") for name in ("open", "create", "mkdir", "remove", "rename")),
        "c": tuple(Entry(name) for name in ("fopen", "open", "opendir", "remove", "unlink", "rename")),
        "fortran": (Entry("open"),),
        "rexx": tuple(Entry(name) for name in ("stream", "linein", "lineout", "charin", "charout")),
        "go": tuple(Entry(f"os.{name}") for name in ("Open", "OpenFile", "ReadFile", "WriteFile", "Create", "Remove")) + (Entry("filepath.Join"),),
        "csharp": tuple(Entry(f"File.{name}") for name in ("ReadAllText", "ReadAllBytes", "ReadAllLines", "WriteAllText", "Open", "OpenRead", "Create", "Delete"))
        + (Entry("Directory.GetFiles"), Entry("Path.Combine"), Entry("FileStream"), Entry("StreamReader"), Entry("StreamWriter")),
    }, names_words=INPUT_WORDS),

    Call_Check("RULE-05-SECRET-LOGGING", "Secrets are not printed or logged", "info", {
        "python": (Entry("print"),) + log_calls(PYTHON_LOGGERS, LOG_METHODS),
        "typescript": log_calls(("console", "logger"), LOG_METHODS),
        "rust": tuple(Entry(name) for name in ("println", "eprintln", "print", "eprint", "dbg", "info", "warn", "error", "debug", "trace")),
        "hare": tuple(Entry(f"fmt.{name}") for name in ("print", "println", "printf", "printfln", "error", "errorln", "errorf", "errorfln")),
        "c": tuple(Entry(name) for name in ("printf", "fprintf", "puts", "syslog")),
        "fortran": (Entry("print"), Entry("write")),
        "rexx": (Entry("say"), Entry("lineout")),
        "go": tuple(Entry(f"{package}.{name}") for package in ("fmt", "log") for name in ("Print", "Println", "Printf", "Fatal", "Fatalf", "Panic", "Panicf")),  # every print or fatal-error function of fmt and log
        "csharp": (Entry("Console.WriteLine"), Entry("Console.Write"), Entry("Debug.WriteLine"), Entry("Trace.WriteLine"))
        + log_calls(("logger", "_logger"), ("LogTrace", "LogDebug", "LogInformation", "LogWarning", "LogError", "LogCritical")),
    }, names_words=SECRET_WORDS),

    Call_Check("RULE-05-WEAK-CIPHER", "No broken encryption (DES, RC4, ECB mode)", "warn", {
        "python": tuple(Entry(name) for name in ("DES.new", "DES3.new", "ARC4.new", "ARC2.new", "Blowfish.new", "algorithms.TripleDES",
                                                 "algorithms.ARC4", "algorithms.Blowfish", "modes.ECB")) + (Entry("AES.new", ("MODE_ECB",)),),
        "typescript": tuple(Entry(name) for name in ("createCipher", "crypto.createCipher", "createDecipher", "crypto.createDecipher"))
        # two loops: each cipher function gets one entry per broken algorithm, since an entry's must_contain parts all have to match
        + tuple(Entry(name, (algorithm,)) for name in ("createCipheriv", "crypto.createCipheriv", "createDecipheriv", "crypto.createDecipheriv")
                for algorithm in BROKEN_NODE_CIPHERS),

        "rust": tuple(Entry(name) for name in ("Des.new", "Des.new_from_slice", "TdesEde3.new", "Rc4.new")),
        "c": tuple(Entry(name) for name in ("DES_ecb_encrypt", "DES_set_key", "RC4", "RC4_set_key", "EVP_des_ecb", "EVP_des_cbc", "EVP_des_ede3",
                                            "EVP_rc4", "EVP_aes_128_ecb", "EVP_aes_192_ecb", "EVP_aes_256_ecb")),
        "go": (Entry("des.NewCipher"), Entry("des.NewTripleDESCipher"), Entry("rc4.NewCipher")),
        "csharp": tuple(Entry(name) for name in ("DES.Create", "TripleDES.Create", "RC2.Create", "DESCryptoServiceProvider",
                                                 "TripleDESCryptoServiceProvider", "RC2CryptoServiceProvider")),
    }),

    Call_Check("RULE-05-OPEN-ACCESS", "No world-writable files or any-website (CORS) access", "warn", {
        "python": mode_calls(("os.chmod", "os.mkdir", "os.makedirs"), WIDE_OPEN_PYTHON)
        + (Entry("CORSMiddleware", ("allow_origins=['*']",)), Entry("CORS", ("origins='*'",)), Entry(ANY_NAME, (CORS_HEADER, "'*'"))),
        "typescript": mode_calls(("fs.chmod", "fs.chmodSync", "chmod", "chmodSync"), ("777", "666"))
        + (Entry("cors", ("cors()",)), Entry("cors", ("origin:'*'",)), Entry("cors", ('origin:"*"',)),
           Entry(ANY_NAME, (CORS_HEADER, '"*"')), Entry(ANY_NAME, (CORS_HEADER, "'*'"))),

        "rust": any_call_with("mode(0o777)", "mode(0o666)", "permissive()", ".allow_any_origin()", "allow_origin(Any)"),
        "c": mode_calls(("chmod", "mkdir"), WIDE_OPEN_C),
        "go": mode_calls(("os.Chmod", "os.Mkdir", "os.MkdirAll", "os.WriteFile", "os.OpenFile"), WIDE_OPEN_C)
        + any_call_with('"' + CORS_HEADER + '","*"', "AllowAllOrigins:true", 'AllowOrigins:[]string{"*"}', "cors.Default()", "cors.New()", "middleware.CORS()"),
        "csharp": (Entry("File.SetUnixFileMode", ("OtherWrite",)),) + any_call_with("AllowAnyOrigin()"),
    }),
]

# Deor code is judged by its standard library's functions, and its `rust` blocks by the Rust entries.
# Mojo calls into Python libraries, so it is judged by the Python entries.
DEOR_ENTRIES = {
    "RULE-05-WEAK-RANDOM": tuple(Entry(name) for name in ("m_rand_int", "m_rand_float", "m_rand_bool")),
    "RULE-05-USER-PATHS": tuple(Entry(name) for name in ("f_read", "f_write", "f_append", "f_exists", "f_lines", "f_delete")),
    "RULE-05-SECRET-LOGGING": (Entry("print"),),
}

for check in CALL_CHECKS:
    check.entries["deor"] = check.entries["rust"] + DEOR_ENTRIES.get(check.id, ())
    check.entries["mojo"] = check.entries["python"]
