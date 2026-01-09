import pytest

from aviation_text_normalizer.fsms.runway import RunwayFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step,conf_min",
    [
        (["runway", "34L"], 0, "RWY 34L", "runway", 2, 0.9),
        (["rwy", "22R"], 0, "RWY 22R", "runway", 2, 0.9),
        (["runway", "three", "four", "left"], 0, "RWY 34L", "left", 4, 0.8),
        (["34L"], 0, "RWY 34L", "left", 1, 0.7),  # direct match low confidence
    ],
)
def test_runway_match(tokens, idx, code, spoken_part, step, conf_min):
    fsm = RunwayFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step
    assert r.confidence >= conf_min


def test_runway_no_match_plain_number():
    fsm = RunwayFSM()
    assert fsm.match(["34"], 0) is None
