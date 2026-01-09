import pytest

from aviation_text_normalizer.fsms.flight_level import FlightLevelFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["fl330"], 0, "FL330", "flight level", 1),
        (["fl", "330"], 0, "FL330", "flight level", 2),
        (["flight", "level", "three", "three", "zero"], 0, "FL330", "flight level", 5),
        (["flight", "level", "3", "3", "0"], 0, "FL330", "flight level", 5),
    ],
)
def test_flight_level_match(tokens, idx, code, spoken_part, step):
    fsm = FlightLevelFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_flight_level_no_match():
    fsm = FlightLevelFSM()
    assert fsm.match(["flight", "levels", "330"], 0) is None
