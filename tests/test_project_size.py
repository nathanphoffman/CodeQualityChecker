from codequality.rules.project_size import size_score

def test_the_curve_hits_its_anchor_points():
    assert size_score(3) == size_score(4) == 1.0
    assert abs(size_score(6) - 0.90) < 1e-9
    assert abs(size_score(7) - 0.62) < 1e-9
    assert abs(size_score(8) - 0.03) < 1e-9

def test_the_curve_only_goes_down_and_ends_near_zero():
    scores = [size_score(power / 10) for power in range(30, 100)]
    assert scores == sorted(scores, reverse=True)
    assert size_score(9) < 0.0001
