from rapdna.experiments.families import families
from rapdna.rhymes.match import build_line
from rapdna.text.phonetics import Lexicon

TH = {"clausal": 4.2, "clausal_end": 1.0, "in_word": 7.9, "consonance": float("inf")}


def test_aabb_and_abab_schemes():
    words = ["kasa", "masa", "tango", "bagno", "dom", "tom", "kosz", "nosz"]
    lx = Lexicon()
    lx.load(set(words))
    line = lambda t: build_line([(w, lx[w], w, "X") for w in t.split()])
    aabb = [line("idzie kasa"), line("wielka masa"), line("polskie tango"), line("grząskie bagno")]
    assert families(aabb, TH).scheme == "AABB"
    abab = [line("idzie kasa"), line("polskie tango"), line("wielka masa"), line("grząskie bagno")]
    assert families(abab, TH).scheme == "ABAB"
