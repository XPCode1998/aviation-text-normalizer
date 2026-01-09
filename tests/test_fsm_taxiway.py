import pytest

from aviation_text_normalizer.fsms.taxiway import TaxiwayFSM


@pytest.mark.parametrize(
    "tokens,idx,code,spoken_part,step",
    [
        (["taxiway", "M6"], 0, "TWY M6", "taxiway", 2),
        (["twy", "A12"], 0, "TWY A12", "taxiway", 2),
        (["taxiway", "alpha", "one", "two"], 0, "TWY A12", "alpha", 4),
        (["taxiway", "mike", "six"], 0, "TWY M6", "mike", 3),
    ],
)
def test_taxiway_match(tokens, idx, code, spoken_part, step):
    fsm = TaxiwayFSM()
    r = fsm.match(tokens, idx)
    assert r is not None
    assert r.entity.code == code
    assert spoken_part in r.entity.spoken
    assert r.step == step


def test_taxiway_requires_prefix():
    # 设计上：不带 taxiway 前缀不匹配（避免与 callsign/其它冲突）
    fsm = TaxiwayFSM()
    assert fsm.match(["mike", "six"], 0) is None
