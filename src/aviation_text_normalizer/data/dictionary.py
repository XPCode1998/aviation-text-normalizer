"""Shared dictionaries for FSM rules."""

ICAO_ALPHABET = {
    "alpha": "A",
    "bravo": "B",
    "charlie": "C",
    "delta": "D",
    "echo": "E",
    "foxtrot": "F",
    "golf": "G",
    "hotel": "H",
    "india": "I",
    "juliett": "J",
    "kilo": "K",
    "lima": "L",
    "mike": "M",
    "november": "N",
    "oscar": "O",
    "papa": "P",
    "quebec": "Q",
    "romeo": "R",
    "sierra": "S",
    "tango": "T",
    "uniform": "U",
    "victor": "V",
    "whiskey": "W",
    "xray": "X",
    "x-ray": "X",
    "yankee": "Y",
    "zulu": "Z",
}
ICAO_REVERSE = {v: k for k, v in ICAO_ALPHABET.items()}

# Aviation number words (superset of your original mapping)
NUMBER_WORDS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "tree": 3,
    "four": 4,
    "five": 5,
    "fife": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "ait": 8,
    "nine": 9,
    "niner": 9,
}
NUMBER_REVERSE = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
}

DECIMAL_WORDS = {"decimal", "point", "dot"}

AIRLINE_ICAO = {
    "CSN": "china southern",
    "CCA": "air china",
    "CES": "china eastern",
}
