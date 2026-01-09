import pytest

from aviation_text_normalizer.fsms.qnh import QNHFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["qnh", "1013"], 0, "QNH 1013", "qnh", 2),
        (["qnh", "one", "zero", "one", "three"], 0, "QNH 1013", "qnh", 5),
        (["qnh", "1", "0", "1", "3"], 0, "QNH 1013", "qnh", 5),
    ],
)
def test_qnh_match(tokens, idx, code, spoken_part, step):
    fsm = QNHFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_qnh_no_match_wrong_length():
    fsm = QNHFSM()
    assert fsm.match(["qnh", "one", "zero"], 0) is None
