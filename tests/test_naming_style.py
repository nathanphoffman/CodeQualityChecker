from pathlib import Path

from codequality import report
from codequality.detect import detect
from codequality.models import Status
from codequality.registry import all_rules
from codequality.rules.rule_02_clear_names.shared.find_names import find_kinded_names
from codequality.rules.rule_02_clear_names.shared.name_styles import CONSTANT, FUNCTION, TYPE, VALUE, VARIABLE, VARIANT, best_convention, follows, MY_CONVENTION

RULE_ID = "RULE-02-NAMING-STYLE"

KINDS_BY_LANGUAGE = {
    "python": ("MAX_TRIES = 3\nclass User_Account:\n    limit = 1\ndef fetch_user(user_id):\n    total = 1\n",
               {"User_Account": TYPE, "fetch_user": FUNCTION, "MAX_TRIES": VALUE, "user_id": VARIABLE, "total": VARIABLE}),
    "rust": ("const MAX_TRIES: i32 = 3;\nstruct UserAccount;\nfn fetch_user(user_id: i32) { let total = 1; }\n",
             {"MAX_TRIES": CONSTANT, "UserAccount": TYPE, "fetch_user": FUNCTION, "user_id": VARIABLE, "total": VARIABLE}),
    "typescript": ("const maxTries = 3;\nlet total = 1;\nclass UserAccount {}\nfunction fetchUser(userId: number) {}\n",
                   {"maxTries": VALUE, "total": VARIABLE, "UserAccount": TYPE, "fetchUser": FUNCTION, "userId": VARIABLE}),
    "hare": ("def MAX_TRIES: int = 3;\ntype point = struct { x: int };\nfn fetch_user(user_id: int) int = { let total = 1; };\n",
             {"MAX_TRIES": CONSTANT, "point": TYPE, "fetch_user": FUNCTION, "user_id": VARIABLE, "total": VARIABLE}),
    "c": ("#define MAX_TRIES 3\nstruct point { int x; };\nint fetch_user(int user_id) { int total = 1; return total; }\n",
          {"MAX_TRIES": CONSTANT, "point": TYPE, "fetch_user": FUNCTION, "user_id": VARIABLE, "total": VARIABLE}),
    "go": ("package main\nconst MaxTries = 3\ntype User struct { Name string }\nfunc FetchUser(userID int) { total := 1 }\n",
           {"MaxTries": CONSTANT, "User": TYPE, "FetchUser": FUNCTION, "userID": VARIABLE, "total": VARIABLE}),
    "csharp": ("class UserAccount { public int Balance { get; set; } void Fetch(int userId) { int total = 1; } }\n",
               {"UserAccount": TYPE, "Balance": VALUE, "Fetch": FUNCTION, "userId": VARIABLE, "total": VARIABLE}),
    "mojo": ("struct Point:\n    var x: Int\nfn fetch_user(user_id: Int):\n    var total = 1\n",
             {"Point": TYPE, "fetch_user": FUNCTION, "user_id": VARIABLE}),
    "fortran": ("program p\ninteger :: total\nend program p\n", {"total": VARIABLE}),
    "rexx": ("fetch: procedure\ntotal = 1\nreturn\n", {"fetch": FUNCTION, "total": VARIABLE}),
    "deor": ("struct Account\n    string owner\n\nfn int fetch_user(int user_id)\n    int total = 1\n    return total\n",
             {"Account": TYPE, "fetch_user": FUNCTION, "user_id": VARIABLE, "total": VARIABLE}),
}

def grade(root: Path, filename: str, source: str):
    (root / filename).write_text(source)

    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[RULE_ID]

def test_every_language_labels_the_kind_of_each_name():
    for language, (source, expected) in KINDS_BY_LANGUAGE.items():
        found = dict(find_kinded_names(source, language))

        assert expected.items() <= found.items(), f"{language}: {found}"

ENUMS = {
    "rust": ("enum Color { Red, Green(i32), Blue { x: i32 } }\n", {"Red", "Green", "Blue"}),
    "typescript": ("enum Color { Red, Green = 2 }\n", {"Red", "Green"}),
    "hare": ("type color = enum { RED, GREEN = 2 };\n", {"RED", "GREEN"}),
    "deor": ("enum Color\n    Red\n    Green\n", {"Red", "Green"}),
}

def test_enum_members_are_found_as_variants():
    for language, (source, members) in ENUMS.items():
        found = {name for name, kind in find_kinded_names(source, language) if kind == VARIANT}

        assert found == members, f"{language}: {found}"

def test_each_language_styles_its_enum_members_its_own_way():
    assert best_convention([("Red", VARIANT), ("DarkBlue", VARIANT)], "rust")[2] == 1.0
    assert best_convention([("RED", VARIANT), ("DARK_BLUE", VARIANT)], "hare")[2] == 1.0
    assert best_convention([("Red", VARIANT), ("red", VARIANT)], "typescript")[2] == 0.5

def test_underscores_around_a_name_do_not_count():
    assert follows("__init__", FUNCTION, MY_CONVENTION)
    assert follows("_private", VARIABLE, MY_CONVENTION)
    assert follows("_", VARIABLE, MY_CONVENTION)

def test_your_convention_checks_each_kind_of_name():
    assert follows("User_Account", TYPE, MY_CONVENTION)
    assert not follows("UserAccount", TYPE, MY_CONVENTION)
    assert follows("MAX_RETRY_COUNT", CONSTANT, MY_CONVENTION)
    assert not follows("maxRetryCount", CONSTANT, MY_CONVENTION)
    assert follows("fetch_user_profile", FUNCTION, MY_CONVENTION)
    assert not follows("fetchUserProfile", FUNCTION, MY_CONVENTION)

def test_the_better_fit_wins_and_a_name_matching_both_is_not_counted_twice():
    names = [("User_Account", TYPE), ("Order_Item", TYPE), ("Total_Sum", TYPE), ("OrderLine", TYPE)]
    label, _, share = best_convention(names, "python")

    assert (label, share) == ("your", 0.75)  # 3 of 4 on yours, only 1 of 4 on Python's

def test_the_language_style_wins_when_it_fits_better():
    names = [("UserAccount", TYPE), ("OrderItem", TYPE), ("TotalSum", TYPE), ("Order_Line", TYPE)]
    label, _, share = best_convention(names, "python")

    assert (label, share) == ("python's", 0.75)

def test_a_language_with_no_standard_style_is_judged_only_by_yours():
    label, _, share = best_convention([("fetch_user", FUNCTION), ("fetchUser", FUNCTION)], "deor")

    assert (label, share) == ("your", 0.5)

def test_python_in_its_own_style_scores_full(tmp_path: Path):
    result = grade(tmp_path, "app.py", "MAX_TRIES = 3\n\nclass UserAccount:\n    pass\n\ndef fetch_user(user_id):\n    return user_id\n")

    assert result.status == Status.PASS

def test_python_in_neither_style_scores_badly(tmp_path: Path):
    result = grade(tmp_path, "app.py", "class user_account:\n    pass\n\ndef FetchUser(userId):\n    maxTries = 3\n    return userId\n")

    assert result.score < 0.5
    assert "FetchUser" in result.message

def test_typescript_camel_case_is_not_penalised(tmp_path: Path):
    result = grade(tmp_path, "app.ts", "export function fetchUser(userId: number) {\n  const maxTries = 3;\n  return userId + maxTries;\n}\n")

    assert result.status == Status.PASS

def test_mixed_projects_are_graded_by_the_share_of_all_names(tmp_path: Path):
    (tmp_path / "good.py").write_text("def fetch_user(user_id):\n    return user_id\n")
    result = grade(tmp_path, "bad.py", "def FetchUser(UserId):\n    return UserId\n")

    assert 0.0 < result.score < 1.0
