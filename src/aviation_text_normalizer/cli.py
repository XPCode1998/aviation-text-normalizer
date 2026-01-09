from __future__ import annotations

import argparse
import logging

from aviation_text_normalizer.core.entity import RenderMode
from aviation_text_normalizer.core.parser import Parser
from aviation_text_normalizer.fsms import DEFAULT_FSMS


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    ap = argparse.ArgumentParser()
    ap.add_argument("text", type=str, help="ATC/RTF text to normalize")
    ap.add_argument(
        "--mode",
        choices=[m.value for m in RenderMode],
        default=RenderMode.SPOKEN.value,
    )
    args = ap.parse_args()

    parser = Parser(fsms=DEFAULT_FSMS)
    print(parser.parse(args.text, mode=RenderMode(args.mode)))
