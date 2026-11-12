from codequality.report.grouping import GROUP_POSITIONS, LANGUAGE_GROUP, group_key, group_weight

def test_weight_falls_with_rule_number():
    assert group_weight("RULE-01") == 1
    assert group_weight(LANGUAGE_GROUP) == 1 / 8
    assert group_weight("RULE-02") > group_weight("RULE-03")

def test_every_language_and_framework_check_is_one_group():
    assert group_key("TS-REACT-001") == group_key("PYTHON-001") == LANGUAGE_GROUP

def test_one_job_is_rule_eight():
    assert GROUP_POSITIONS["RULE-04"] == 8
