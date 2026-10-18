import pytest

from rapdna.phonology.features import similarity
from rapdna.phonology.syllables import stressed_index, syllabify
from rapdna.rhymes.hb_detect import rhyme_type
from rapdna.rhymes.hb import RhymeModel, make_tail
from rapdna.rhymes.patterns import count_syllables, phonemes
from rapdna.text.phonetics import Lexicon, tokenize


@pytest.fixture(scope="module")
def lex():
    lx = Lexicon()
    lx.load({"misia", "pisia", "domu", "tomu", "miłość", "siłą", "trzeba", "czeka", "bagno", "tango",
             "polskie", "grząskie", "naughty", "dżungla"})
    return lx


def tail(lex, *words):
    return make_tail([(w, lex[w]) for w in words])


def test_normalization_matches_panphon_inventory():
    assert phonemes("tʃˈɛba") == ["t͡ʂ", "ˈ", "ɛ", "b", "a"]
    assert phonemes("ɕˈiwɔ̃") == ["ɕ", "ˈ", "i", "w", "ɔ̃"]


def test_panphon_similarity_orders_pairs():
    assert similarity("p", "b") > similarity("p", "r")
    assert similarity("ɔ", "ɔ̃") > similarity("ɔ", "i")


def test_syllabify_and_stress(lex):
    s = syllabify(lex["tango"])
    assert [x.nucleus for x in s] == ["a", "ɔ"] and stressed_index(s) == 0


def test_rhyme_types(lex):
    assert rhyme_type(tail(lex, "misia"), tail(lex, "pisia")) == "exact"
    assert rhyme_type(tail(lex, "domu"), tail(lex, "tomu")) == "exact"
    assert rhyme_type(tail(lex, "tango"), tail(lex, "bagno")) == "assonance"


def test_multisyllabic_length(lex):
    m = RhymeModel({}, {})  # no tables: scores from PanPhon similarity
    assert m.length(tail(lex, "polskie", "tango"), tail(lex, "grząskie", "bagno")) >= 3


def test_score_prefers_rhyme(lex):
    m = RhymeModel({}, {})
    assert m.score(tail(lex, "domu"), tail(lex, "tomu")) > m.score(tail(lex, "domu"), tail(lex, "miłość"))


def test_syllables(lex):
    assert count_syllables(lex["miłość"]) == 2
    assert count_syllables(lex["dżungla"]) == 2


def test_english_fallback(lex):
    assert lex.lang["naughty"] == "en"
    assert count_syllables(lex["naughty"]) == 2


def test_tokenize_numbers():
    assert tokenize("W latach 90' nie") == ["W", "latach", "dziewięćdziesiąt", "nie"]


def test_language_rules():
    from rapdna.text.phonetics import english_loan, polish_in_english_line

    assert english_loan("beat") and english_loan("trap") and english_loan("hype")
    assert not english_loan("won") and not english_loan("fury") and not english_loan("my")  # Polish words
    assert polish_in_english_line("jej") and polish_in_english_line("żaden")
    assert not polish_in_english_line("I") and not polish_in_english_line("money")


def test_language_rules_c_h_context():
    from rapdna.text.phonetics import _en_to_pl, context_english, english_stem, is_english

    assert all(is_english(w, False) for w in ["steve", "scott", "carell", "avengers", "feat", "silver"])
    assert not any(is_english(w, False) for w in ["agata", "toronto", "valentino", "by", "my", "one"])
    assert english_stem("shotgunem") == ("shotgun", "ɛm") and english_stem("wolverinem") == ("wolverine", "ɛm")
    assert english_stem("wave'm") == ("wave", "ɛm")
    assert english_stem("dla") is None and english_stem("tobie") is None and english_stem("agata") is None
    assert context_english("I'll be back".split(), [True, False, True]) == [True, True, True]
    assert context_english("Bear Grylls".split(), [False, True]) == [True, True]
    assert context_english("na mainstream z shotgunem".split(), [False, True, False, True])[2] is False
    assert _en_to_pl("skˈɑːt", "scott") == "skˈɔt" and _en_to_pl("sɪnˈɑːtɹə", "sinatra") == "sinˈatra"
    assert _en_to_pl("sˈɜːfɚ", "surfer") == "sˈɛrfɛr"
