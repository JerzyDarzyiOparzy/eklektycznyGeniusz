import pytest

from rapdna.rhymes.hb import RhymeModel, make_tail
from rapdna.experiments.units import rhyme_units, score
from rapdna.text.phonetics import Lexicon

WORDS = {"tango", "bagno", "kasa", "masa", "kosa", "teatr", "nauka", "siano", "polskie", "grząskie", "domu", "miłość"}


@pytest.fixture(scope="module")
def lex():
    lx = Lexicon()
    lx.load(WORDS)
    return lx


def show(lex, *words):
    return [str(u) for u in rhyme_units([(w, lex[w]) for w in words])]


def test_units_cut_before_vowel(lex):
    assert show(lex, "tango") == ["aŋɡ", "ɔ"]
    assert show(lex, "bagno") == ["aɡn", "ɔ"]
    assert show(lex, "kasa") == show(lex, "masa") == ["as", "a"]
    assert show(lex, "kosa") == ["ɔs", "a"]


def test_units_adjacent_vowels(lex):
    assert show(lex, "siano") == ["an", "ɔ"]  # „i” only softens
    assert show(lex, "teatr") == ["ɛ", "atr"]  # two adjacent vowels
    assert show(lex, "nauka") == ["uk", "a"]  # the rhyme starts at the stress: na-U-ka


def test_rhyme_starts_at_last_word_stress(lex):
    assert show(lex, "polskie", "tango") == show(lex, "tango")


def test_unit_score_equals_model_score(lex):
    m = RhymeModel({}, {})  # no tables: scores from PanPhon similarity
    pairs = [("tango", "bagno"), ("kasa", "masa"), ("kasa", "kosa"), ("domu", "miłość"), ("teatr", "nauka")]
    for a, b in pairs:
        t1, t2 = make_tail([(a, lex[a])]), make_tail([(b, lex[b])])
        assert score(m, t1, t2) == pytest.approx(m.score(t1, t2), abs=1e-9)
