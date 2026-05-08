from positives import summarize_positives


def test_list_inputs_still_work() -> None:
    assert summarize_positives([2, -1, 3]) == (2, [2, 3])


def test_generator_inputs_match_list_behavior() -> None:
    values = (value for value in [2, -1, 3])
    assert summarize_positives(values) == (2, [2, 3])
