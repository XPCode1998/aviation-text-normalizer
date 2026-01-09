import pytest

from aviation_text_normalizer.core.entity import RenderMode
from aviation_text_normalizer.core.parser import Parser
from aviation_text_normalizer.fsms import DEFAULT_FSMS


@pytest.fixture()
def parser() -> Parser:
    return Parser(fsms=DEFAULT_FSMS)


@pytest.fixture()
def modes():
    return (RenderMode.CODE, RenderMode.SPOKEN)
