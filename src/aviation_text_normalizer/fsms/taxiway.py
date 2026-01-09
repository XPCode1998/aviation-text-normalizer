from __future__ import annotations

import re
from typing import Optional

from aviation_text_normalizer.core.entity import AviationEntity, EntityType
from aviation_text_normalizer.core.match import MatchResult
from aviation_text_normalizer.data.dictionary import ICAO_ALPHABET, ICAO_REVERSE
from aviation_text_normalizer.utils.number_utils import digits_to_spoken, token_to_digit

_TW_PREFIX = {"taxiway", "twy", "tw"}
_TW_CODE_RE = re.compile(r"^[A-Z](\d{1,2})?$")


class TaxiwayFSM:
    """
    Taxiway:
    - taxiway M6 / twy A12 / taxiway A
    - taxiway mike six / taxiway alpha one two
    - M6 (if preceded by taxiway; direct M6 is intentionally not matched)
    """

    def match(self, tokens: list[str], index: int) -> Optional[MatchResult]:
        if index >= len(tokens):
            return None

        start = index
        has_prefix = False
        if tokens[index].lower() in _TW_PREFIX and index + 1 < len(tokens):
            start = index + 1
            has_prefix = True

        if not has_prefix:
            return None

        # Code: M6 / A12 / A
        t = tokens[start].upper()
        if _TW_CODE_RE.fullmatch(t):
            letter = t[0]
            digits = t[1:] if len(t) > 1 else ""
            raw = " ".join(tokens[index : start + 1])
            code = f"TWY {letter}{digits}"
            spoken = f"taxiway {ICAO_REVERSE.get(letter, letter)}"
            if digits:
                spoken += f" {digits_to_spoken(digits)}"
            entity = AviationEntity(
                type=EntityType.TAXIWAY,
                raw=raw,
                code=code,
                spoken=spoken,
                confidence=0.90,
            )
            return MatchResult(entity=entity, step=start - index + 1, confidence=0.90)

        # Spoken: mike six / alpha one two
        w0 = tokens[start].lower()
        if w0 in ICAO_ALPHABET:
            letter = ICAO_ALPHABET[w0]
            j = start + 1
            digs: list[str] = []
            while j < len(tokens) and len(digs) < 2:
                d = token_to_digit(tokens[j])
                if d is None:
                    break
                digs.append(d)
                j += 1

            raw = " ".join(tokens[index:j])
            code = f"TWY {letter}{''.join(digs)}"
            spoken = f"taxiway {w0}"
            if digs:
                spoken += f" {digits_to_spoken(''.join(digs))}"

            entity = AviationEntity(
                type=EntityType.TAXIWAY,
                raw=raw,
                code=code,
                spoken=spoken,
                confidence=0.90,
            )
            return MatchResult(entity=entity, step=j - index, confidence=0.90)

        return None
