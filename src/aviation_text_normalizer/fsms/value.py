from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.data.dictionary import DECIMAL_WORDS
from aviation_text_normalizer.utils.number_utils import num_str_to_spoken, token_to_digit

_NUM_RE = re.compile(r"^\d+(\.\d+)?$")

_UNIT = {
    "ft": ("ft", "feet"),
    "feet": ("ft", "feet"),
    "foot": ("ft", "feet"),
    "kt": ("kt", "knots"),
    "kts": ("kt", "knots"),
    "knot": ("kt", "knots"),
    "knots": ("kt", "knots"),
    "deg": ("deg", "degrees"),
    "degree": ("deg", "degrees"),
    "degrees": ("deg", "degrees"),
}


class ValueFSM:
    """
    Generic value + unit:
    - 5.5 ft
    - five decimal five feet
    - 250 kt
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        if index >= len(tokens):
            return None

        # Code: 5.5 ft
        if (
            index + 1 < len(tokens)
            and _NUM_RE.fullmatch(tokens[index])
            and tokens[index + 1].lower() in _UNIT
        ):
            num = tokens[index]
            u_code, u_spk = _UNIT[tokens[index + 1].lower()]
            raw = " ".join(tokens[index : index + 2])
            entity = AviationEntity(
                type=EntityType.VALUE,
                raw=raw,
                code=f"{num} {u_code}",
                spoken=f"{num_str_to_spoken(num)} {u_spk}",
                confidence=0.90,
            )
            return MatchResult(entity=entity, step=2, confidence=0.90)

        # Spoken: five decimal five feet
        j = index
        major: list[str] = []
        while j < len(tokens) and len(major) < 6:
            d = token_to_digit(tokens[j])
            if d is None:
                break
            major.append(d)
            j += 1

        if not major:
            return None

        frac: list[str] = []
        if j < len(tokens) and tokens[j].lower() in DECIMAL_WORDS:
            j += 1
            while j < len(tokens) and len(frac) < 6:
                d = token_to_digit(tokens[j])
                if d is None:
                    break
                frac.append(d)
                j += 1

        if j < len(tokens) and tokens[j].lower() in _UNIT:
            u_code, u_spk = _UNIT[tokens[j].lower()]
            j += 1

            num = "".join(major) + (("." + "".join(frac)) if frac else "")
            raw = " ".join(tokens[index:j])
            entity = AviationEntity(
                type=EntityType.VALUE,
                raw=raw,
                code=f"{num} {u_code}",
                spoken=f"{num_str_to_spoken(num)} {u_spk}",
                confidence=0.85,
            )
            return MatchResult(entity=entity, step=j - index, confidence=0.85)

        return None
