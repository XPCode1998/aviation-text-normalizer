import pytest

from aviation_text_normalizer.fsms.heading import HeadingFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken,step",
    [
        (["heading", "270"], 0, "HDG 270", "heading", 2),
        (["hdg", "090"], 0, "HDG 090", "heading", 2),
        (["heading", "two", "seven", "zero"], 0, "HDG 270", "heading", 4),
        (["heading", "2", "7", "0"], 0, "HDG 270", "heading", 4),
    ],
)
def test_heading_match(tokens, idx, code, spoken, step):
    fsm = HeadingFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken in r.entity.spoken
    assert r.step == step


def test_heading_no_match():
    fsm = HeadingFSM()
    assert fsm.match(["heading"], 0) is None
