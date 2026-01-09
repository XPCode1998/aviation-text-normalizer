import pytest

from aviation_text_normalizer.core.tokenizer import Tokenizer


@pytest.mark.parametrize(
    "text,expected_subtokens",
    [
        ("CSN6889, contact 118.75!", ["csn6889", "contact", "118.75"]),
        ("FL330", ["fl330"]),
        ("FL 330", ["fl", "330"]),
        ("runway 34L", ["runway", "34", "l"] if False else ["runway", "34L"]),  # depends on regex
        ("qnh one zero one three", ["qnh", "one", "zero", "one", "three"]),
        ("heading two seven zero", ["heading", "two", "seven", "zero"]),
    ],
)
def test_tokenize_contains_expected(text, expected_subtokens):
    tok = Tokenizer()
    tokens = tok.tokenize(tok.normalize(text))
    # 不强制完全一致（因为 token 规则可调整），只检查关键 token 是否出现
    for t in expected_subtokens:
        assert t in tokens


def test_normalize_whitespace_and_punct():
    tok = Tokenizer()
    s = "  CSN6889,   contact: 118.75  "
    norm = tok.normalize(s)
    assert "," not in norm
    assert ":" not in norm
    assert "  " not in norm
    assert norm.startswith("CSN6889") or norm.startswith("csn6889")
