from codequality.report.grouping import letter

def test_signs_inside_each_band():
    assert [letter(score) for score in (90, 92.9, 93, 97.9, 98, 100)] == ["A-", "A-", "A", "A", "A+", "A+"]
    assert [letter(score) for score in (80, 83, 88)] == ["B-", "B", "B+"]
    assert [letter(score) for score in (70, 75, 79)] == ["C-", "C", "C+"]
    assert [letter(score) for score in (60, 65, 69.9)] == ["D-", "D", "D+"]

def test_f_has_no_sign():
    assert letter(59.9) == "F" and letter(0) == "F"
