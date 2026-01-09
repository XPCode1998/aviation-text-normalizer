import pytest

from aviation_text_normalizer.fsms.frequency import FrequencyFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["118.75"], 0, "118.75", "decimal", 1),
        (["contact", "118.75"], 0, "118.75", "decimal", 2),
        (["one", "one", "eight", "decimal", "seven", "five"], 0, "118.75", "decimal", 6),
        (["contact", "one", "one", "eight", "point", "seven", "five"], 0, "118.75", "decimal", 7),
    ],
)
def test_frequency_match(tokens, idx, code, spoken_part, step):
    fsm = FrequencyFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_frequency_no_match():
    fsm = FrequencyFSM()
    assert fsm.match(["118", "75"], 0) is None
