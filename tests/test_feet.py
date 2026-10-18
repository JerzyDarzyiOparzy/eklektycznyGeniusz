from rapdna.experiments import feet
from rapdna.rhymes.match import build_line


def _line(words):
    return build_line([(f, ipa, f, "X") for f, ipa in words])


def test_candidates_feet_and_merges():
    line = _line([("to", "tˈɔ"), ("przy", "pʃˈɨ"), ("skroni", "skrˈɔɲi"), ("koszmarem", "kɔʃmˈarɛm")])
    cells = {(c.text, c.kind, "-".join(c.key)) for c in feet.candidates(0, line)}
    assert ("to przy", "join", "ɔ-i") in cells  # short word + the next one
    assert ("skroni", "foot", "ɔ-i") in cells  # word foot
    assert ("koszmarem", "foot", "a-ɛ") in cells and ("koszmarem", "rest", "ɔ") in cells  # kosz | marem


def test_mark_links_parallel_end_feet():
    a = _line([("mówię", "mˈuvjɛ"), ("skroni", "skrˈɔɲi")])
    b = _line([("widzę", "vˈidzɛ"), ("glory", "ɡlˈɔri")])
    marked = feet.mark([a, b])
    assert {c.text for c, _ in marked} >= {"skroni", "glory"}
