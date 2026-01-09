import pytest

from aviation_text_normalizer.fsms.value import ValueFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["5000", "ft"], 0, "5000 ft", "feet", 2),
        (["5.5", "ft"], 0, "5.5 ft", "decimal", 2),
        (["two", "five", "zero", "kt"], 0, "250 kt", "knots", 4),
        (["five", "decimal", "five", "feet"], 0, "5.5 ft", "decimal", 4),
    ],
)
def test_value_match(tokens, idx, code, spoken_part, step):
    fsm = ValueFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_value_no_match_missing_unit():
    fsm = ValueFSM()
    assert fsm.match(["5000"], 0) is None
