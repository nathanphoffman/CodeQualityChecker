from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

BAD_PYTHON = '''
import os, pickle, yaml, hashlib, random, requests, logging
def bad(user_input, password):
    api_key = "abcd1234efgh5678"
    query = f"SELECT * FROM users WHERE name = {user_input}"
    other = "DELETE FROM t WHERE id = " + user_input
    os.system(user_input)
    eval(user_input)
    pickle.loads(user_input)
    yaml.load(user_input)
    hashlib.md5(b"x")
    token = random.random()
    requests.get("https://x", verify=False)
    open(os.path.join("/data", user_input))
    logging.info(password)
'''

BAD_TYPESCRIPT = '''
const apiKey = "abcd1234efgh5678";
function bad(userInput: string, password: string) {
  const query = `SELECT * FROM users WHERE name = ${userInput}`;
  const other = "DELETE FROM t WHERE id = " + userInput;
  eval(userInput);
  crypto.createHash("md5");
  const token = Math.random();
  https.request({ rejectUnauthorized: false });
  el.innerHTML = userInput;
  fs.readFile(userInput);
  console.log(password);
}
'''

BAD_RUST = '''
fn bad(user_input: String, password: String) {
    let query = format!("SELECT * FROM users WHERE name = {}", user_input);
    Command::new("sh").arg("-c").arg(&user_input);
    let client = Client::builder().danger_accept_invalid_certs(true).build();
    unsafe { dangerous(); }
    let file = File::open(user_input);
    println!("{}", password);
}
'''

EXPECTED = {
    "RULE-05-HARDCODED-SECRETS": ("bad.py", "bad.ts"),
    "RULE-05-SQL-STRINGS": ("bad.py", "bad.ts", "bad.rs"),
    "RULE-05-RUN-STRINGS": ("bad.py", "bad.ts", "bad.rs"),
    "RULE-05-UNSAFE-LOADING": ("bad.py",),
    "RULE-05-WEAK-HASH": ("bad.py", "bad.ts"),
    "RULE-05-WEAK-RANDOM": ("bad.py", "bad.ts"),
    "RULE-05-SAFETY-OFF": ("bad.py", "bad.ts", "bad.rs"),
    "RULE-05-RISKY-OUTPUT": ("bad.ts", "bad.rs"),
    "RULE-05-USER-PATHS": ("bad.py", "bad.ts", "bad.rs"),
    "RULE-05-SECRET-LOGGING": ("bad.py", "bad.ts", "bad.rs"),
}


def grade_bad_project(root: Path):
    (root / "bad.py").write_text(BAD_PYTHON)
    (root / "bad.ts").write_text(BAD_TYPESCRIPT)
    (root / "bad.rs").write_text(BAD_RUST)
    (root / ".env").write_text("X=1\n")
    project = detect(root)
    return {rule.id: result for rule, result in report.run(project, all_rules())}


def test_every_security_check_flags_every_language(tmp_path: Path):
    results = grade_bad_project(tmp_path)
    for rule_id, files in EXPECTED.items():
        for file in files:
            assert f"{file}:" in results[rule_id].message or file in results[rule_id].message, (rule_id, file)


def test_env_file_without_gitignore_is_flagged(tmp_path: Path):
    assert grade_bad_project(tmp_path)["RULE-05-SECRET-FILES"].score == 0.0


def test_env_file_in_gitignore_is_fine(tmp_path: Path):
    (tmp_path / ".gitignore").write_text(".env\n")
    (tmp_path / "ok.py").write_text("x = 1\n")
    (tmp_path / ".env").write_text("X=1\n")
    results = {rule.id: result for rule, result in report.run(detect(tmp_path), all_rules())}
    assert results["RULE-05-SECRET-FILES"].score == 1.0


def test_ordinary_sentences_and_safe_code_pass(tmp_path: Path):
    (tmp_path / "ok.py").write_text(
        "import subprocess\n"
        "def fine(name, conn):\n"
        "    conn.execute('SELECT * FROM users WHERE name = %s', (name,))\n"
        "    subprocess.run(['ls', '-l'])\n"
        "    print(f'Select an item from the list {name}')\n"
    )
    results = grade_bad_project_free(tmp_path)
    assert all(result.score == 1.0 for rule_id, result in results.items() if rule_id.startswith("RULE-05"))


def grade_bad_project_free(root: Path):
    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}
