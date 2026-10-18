from rapdna.experiments import vowel_matrix as M
from rapdna.rhymes.match import build_line


def _line(words):
    return build_line([(f, ipa, f, "NOUN") for f, ipa in words])


def test_end_score_assonance():
    tango, bagno = _line([("tango", "tˈaŋɡɔ")]), _line([("bagno", "bˈaɡnɔ")])
    kasa, kosa = _line([("kasa", "kˈasa")]), _line([("kosa", "kˈɔsa")])
    assert M.end_score(tango, 0, bagno, 0) >= 0  # a-o / a-o: assonance from the stress
    assert M.end_score(kasa, 0, kosa, 0) < 0  # another stressed vowel


def test_vowel_probs_sum_to_one():
    p = M.vowel_probs()
    assert abs(sum(p.values()) - 1) < 1e-6 and p["u"] < p["a"]
