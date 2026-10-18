import pytest

from rapdna.rhymes import rules
from rapdna.rhymes.match import build_line, find, pair_score
from rapdna.text.phonetics import Lexicon

WORDS = ["kasa", "masa", "kosa", "tango", "bagno", "jest", "tekst", "bieda", "woda", "zamek", "zamach", "polskie",
         "grząskie", "ma", "do", "mnie", "skromnie", "zrobiłem", "kupiłem", "rama", "brama", "tama"]


@pytest.fixture(scope="module")
def lex():
    lx = Lexicon()
    lx.load(set(WORDS))
    return lx


def line(lex, text, pos="NOUN"):
    return build_line([(w, lex[w], w, pos) for w in text.split()])


def end_score(lex, a, b):
    la, lb = line(lex, a), line(lex, b)
    return pair_score(la, len(la.forms) - 1, lb, len(lb.forms) - 1)


def test_line_units_cross_word_boundaries(lex):
    ln = line(lex, "polskie tango")
    assert ["".join((k.v, *k.cons)) for k in ln.ks] == ["ɔlsk", "ɛt", "aŋɡ", "ɔ"]
    assert ln.ks[1].coda == () and ln.ks[1].last  # „polskie” ends in a vowel
    assert ln.stress_of_word == {0: 0, 1: 2}


def test_known_cases_kr6(lex):
    # rhymes score clearly higher than non-rhymes (calibration sets the threshold; here only order and sign)
    for a, b in [("kasa", "masa"), ("tango", "bagno"), ("jest", "tekst")]:
        assert end_score(lex, a, b) > 2, (a, b)
    for a, b in [("kasa", "kosa"), ("bieda", "woda"), ("zamek", "zamach")]:
        assert end_score(lex, a, b) <= 0, (a, b)  # 0 = no surplus of matching phonemes


def test_consonant_clusters_aligned_best_not_right(lex):
    # „jest” with „tekst”: s–s and t–t match, k is a gap (the old model aligned from the right)
    assert rules.cluster(("s", "t"), ("k", "s", "t")) == pytest.approx(2 + 2 - 1)
    assert rules.cluster(("s", "t"), ("s",)) == pytest.approx(2 - 1)


def test_multisyllabic_across_words(lex):
    a, b = line(lex, "polskie tango"), line(lex, "grząskie bagno")
    best = max((m for m in find(a, b) if m.anchor == "clausal"), key=lambda m: m.score)
    assert best.syllables == 4


def test_composite_rhyme(lex):
    assert end_score(lex, "do mnie", "skromnie") > 2


def test_ruler_is_fixed():
    # the ruler is rules only, no corpus data
    assert rules.unit("a", ("s",), "a", ("s",)) == 4.0
    assert rules.vowel("ɛ", "ɔ") == rules.OTHER_VOWEL


def test_repeated_words_are_not_part_of_rhyme():
    lx = Lexicon()
    lx.load({"życie", "by", "było", "dziwne", "zimne"})
    a = build_line([(w, lx[w], w, "X") for w in "życie by było dziwne".split()])
    b = build_line([(w, lx[w], w, "X") for w in "życie by było zimne".split()])
    best = max((m for m in find(a, b) if m.anchor == "clausal"), key=lambda m: m.score)
    assert best.syllables == 2  # only „dziwne / zimne”; „życie by było” is a repeat


def test_rhyme_search_index():
    import pandas as pd

    from rapdna.rhymes.search import Index

    lx = Lexicon()
    words = ["tango", "mango", "bagno", "kasa", "klasa", "dom"]
    lx.load(set(words))
    idx = Index(pd.DataFrame({"form": words, "ipa": [lx[w] for w in words]}))
    top = idx.rhymes("tango", lx["tango"], k=3)
    assert top[0][2] == ["mango"]  # the identical tail [aŋɡ ɔ] ranks first
    assert all("kasa" not in ws for _, _, ws in top)  # another stressed vowel is not a rhyme
