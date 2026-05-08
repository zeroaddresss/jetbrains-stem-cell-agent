from positives import summarize_positives


def test_generator_inputs_match_list_behavior() -> None:
    values = (value for value in [2, -1, 3])
    assert summarize_positives(values) == (2, [2, 3])


def test_all_negative_generator_is_supported() -> None:
    values = (value for value in [-3, -2, -1])
    assert summarize_positives(values) == (0, [])


def test_tuple_inputs_are_unchanged() -> None:
    assert summarize_positives((0, 4, 5)) == (2, [4, 5])
