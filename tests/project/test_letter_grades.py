from codequality.report.grouping import letter

def test_signs_inside_each_band():
    assert [letter(score) for score in (90, 92.9, 93, 97.9, 98, 100)] == ["A-", "A-", "A", "A", "A+", "A+"]
    assert [letter(score) for score in (80, 83, 88)] == ["B-", "B", "B+"]
    assert [letter(score) for score in (70, 75, 79)] == ["C-", "C", "C+"]
    assert [letter(score) for score in (60, 65, 69.9)] == ["D-", "D", "D+"]

def test_f_has_no_sign():
    assert letter(59.9) == "F" and letter(0) == "F"

def test_a_score_just_under_perfect_is_never_shown_as_100():
    from codequality.report.grouping import rounded_score, shown_percent

    assert shown_percent(99.95, 1) == "99.9" and shown_percent(99.6) == "99"
    assert shown_percent(100.0, 1) == "100.0" and shown_percent(94.64, 1) == "94.6"
    assert rounded_score(99.99, 1) < 100.0 and rounded_score(100.0, 1) == 100.0

def test_one_double_blank_line_among_many_shows_in_every_output(tmp_path, capsys):
    from codequality.cli import main

    (tmp_path / "lib.deor").write_text("fn int one()\n\treturn 1\n\n" * 600 + "\n\nfn int two()\n\treturn 2\n")

    for flags in ([], ["--quick"], ["--full"]):
        main([str(tmp_path), "--only", "RULE-14-NO-DOUBLE", *flags])
        scored_lines = [line for line in capsys.readouterr().out.splitlines() if "Rule 14" in line or "RULE 14" in line or "RULE-14" in line or "TOTAL SCORE" in line]

        assert scored_lines and not any("100%" in line or "100.0" in line for line in scored_lines), flags

    main([str(tmp_path), "--only", "RULE-14-NO-DOUBLE", "--json"])

    assert '"score": 100.0' not in capsys.readouterr().out
