import pytest

from aviation_text_normalizer.core.entity import RenderMode


@pytest.mark.parametrize(
    "text,expect_code_contains,expect_spoken_contains",
    [
        (
            "CSN6889 climb to FL330 turn right heading 270 contact 118.75 QNH 1013",
            ["CSN6889", "FL330", "HDG 270", "118.75", "QNH 1013"],
            ["china southern", "flight level", "heading", "decimal", "qnh"],
        ),
        (
            "china southern six eight eight nine climb to flight level three three zero contact one one eight decimal seven five",
            ["CSN6889", "FL330", "118.75"],
            ["china southern", "flight level", "decimal"],
        ),
        (
            "taxi via mike six to runway 34L",
            ["TWY M6", "RWY 34L"],
            ["taxiway mike six", "runway three four left"],
        ),
        (
            "qnh one zero one three maintain fl 350",
            ["QNH 1013", "FL350"],
            ["qnh", "flight level"],
        ),
    ],
)
def test_parser_end_to_end(parser, text, expect_code_contains, expect_spoken_contains):
    out_code = parser.parse(text, mode=RenderMode.CODE)
    out_spoken = parser.parse(text, mode=RenderMode.SPOKEN)

    for s in expect_code_contains:
        assert s in out_code
    for s in expect_spoken_contains:
        assert s in out_spoken


def test_parser_robustness_should_not_crash(parser):
    # 混杂噪声、奇怪符号、未知词，目标是“不崩溃”
    text = "### @@ CSN6889 ??? climb---to FL330 !! contact one one eight point seven five QNH niner niner niner"
    out = parser.parse(text, mode=RenderMode.SPOKEN)
    assert isinstance(out, str)
    assert len(out) > 0


def test_mode_switch_changes_output(parser):
    text = "contact 118.75"
    out_code = parser.parse(text, mode=RenderMode.CODE)
    out_spoken = parser.parse(text, mode=RenderMode.SPOKEN)
    assert out_code != out_spoken
    assert "118.75" in out_code
    assert "decimal" in out_spoken
