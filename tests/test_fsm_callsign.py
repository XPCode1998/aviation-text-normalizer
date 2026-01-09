import pytest

from aviation_text_normalizer.fsms.callsign import CallsignFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["csn6889"], 0, "CSN6889", "china southern", 1),
        (["csn", "6889"], 0, "CSN6889", "china southern", 2),
        (["csn", "six", "eight", "eight", "nine"], 0, "CSN6889", "china southern", 5),
        (["china", "southern", "six", "eight", "eight", "nine"], 0, "CSN6889", "china southern", 6),
    ],
)
def test_callsign_match(tokens, idx, code, spoken_part, step):
    fsm = CallsignFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_callsign_no_match():
    fsm = CallsignFSM()
    assert fsm.match(["hello", "world"], 0) is None
