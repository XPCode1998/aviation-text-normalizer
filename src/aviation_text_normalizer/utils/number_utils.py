from __future__ import annotations

from aviation_text_normalizer.data.dictionary import NUMBER_REVERSE, NUMBER_WORDS


def token_to_digit(token: str) -> str | None:
    """
    Convert a token into a single digit char if possible.

    Accepts:
    - "7"
    - "seven", "tree", "fife", "niner", "oh", etc.
    """
    t = token.lower()
    if t.isdigit() and len(t) == 1:
        return t
    if t in NUMBER_WORDS:
        return str(NUMBER_WORDS[t])
    return None


def digits_to_spoken(digits: str) -> str:
    """Convert digit string into aviation spoken words, digit-by-digit."""
    only = "".join(ch for ch in digits if ch.isdigit())
    if not only:
        return ""
    return " ".join(NUMBER_REVERSE[int(ch)] for ch in only)


def num_str_to_spoken(num: str) -> str:
    """Convert integer/decimal number string to spoken form."""
    if "." in num:
        a, b = num.split(".", 1)
        return f"{digits_to_spoken(a)} decimal {digits_to_spoken(b)}"
    return digits_to_spoken(num)
