from rapdna.validate.rhyme_eval import syllable_chars, vowel_positions


def test_vowel_positions_skip_softening_i():
    assert len(vowel_positions("dwadzieścia")) == 3  # dwa-dzieś-cia
    assert len(vowel_positions("wydłuża")) == 3
    assert vowel_positions("siebie") == [2, 5]


def test_syllable_chars_cover_word():
    spans = syllable_chars("wydłuża", 3)
    assert spans[0][0] == 0 and spans[-1][1] == 7
    assert all(a[1] == b[0] for a, b in zip(spans, spans[1:]))  # syllables are adjacent


def test_spelled_acronym():
    from rapdna.text.phonetics import spelled_acronym
    assert spelled_acronym("WKU") == "vukaˈu"
    assert spelled_acronym("SB") == "ɛsˈbɛ"
    assert spelled_acronym("UFO") is None and spelled_acronym("PiS") is None and spelled_acronym("dom") is None


def test_position16():
    from rapdna.validate.recordings import position16
    beats, down = [0, 0.5, 1, 1.5, 2, 2.5, 3], [0, 2]
    assert position16(0.0, beats, down) == 0
    assert position16(1.26, beats, down) == 10  # 3rd beat of the bar, second sixteenth
    assert position16(2.0, beats, down) == 0  # a new bar


def _line(words):
    from rapdna.rhymes.match import build_line
    return build_line([(f, ipa, f, "X") for f, ipa in words])


def test_end_cells_first_and_trailing_filler():
    from rapdna.experiments import feet
    a = _line([("liczą", "lˈitʂɔ̃"), ("na", "na"), ("błąd", "bwˈɔnt")])
    b = _line([("w", "v"), ("zasięgu", "zaɕˈɛŋɡu"), ("ich", "ix"), ("rąk", "rˈɔŋk")])
    c = _line([("widzę", "vˈidzɛ"), ("moskitierę", "mɔskʲitʲˈɛrɛ"), ("i", "i")])
    d = _line([("a", "a"), ("ja", "ja"), ("wierzę", "vʲˈɛʒɛ")])
    ends, links = feet.end_cells([a, b, c, d])
    assert ends[0].text == "błąd" and ends[1].text == "rąk" and (0, 1) in links
    assert ends[2].text == "moskitierę" and (2, 3) in links  # a trailing „i” is not the rhyme


def test_probability_mark_keeps_end_rhymes():
    from rapdna.experiments import probability
    a = _line([("liczą", "lˈitʂɔ̃"), ("na", "na"), ("błąd", "bwˈɔnt")])
    b = _line([("w", "v"), ("zasięgu", "zaɕˈɛŋɡu"), ("ich", "ix"), ("rąk", "rˈɔŋk")])
    cfg = {"weights": {"intercept": -5.0}, "threshold": 0.5}  # nothing inside passes, the end rhyme stays
    marked = probability.mark([a, b], cfg=cfg)
    assert {c.text for c, _, _ in marked} == {"błąd", "rąk"}


def test_line_pairs_mark_parallel_chain_not_single_echo():
    from rapdna.experiments import line_pairs
    a = _line([("masz", "mˈaʃ"), ("mocne", "mˈɔtsnɛ"), ("combo", "kˈɔmbɔ"), ("dzisiaj", "dʑˈiɕaj")])
    b = _line([("mamy", "mˈamɨ"), ("proste", "prˈɔstɛ"), ("motto", "mˈɔttɔ"), ("wszędzie", "fʂˈɛɲdʑɛ")])
    c = _line([("a", "a"), ("ja", "ja"), ("wiem", "vʲˈɛm"), ("dobrze", "dˈɔbʐɛ")])
    marked = {(cell.line, cell.text) for cell, _ in line_pairs.mark([a, b, c])}
    assert {(0, "mocne"), (0, "combo"), (1, "proste"), (1, "motto")} <= marked
    assert not any(line == 2 and text == "wiem" for line, text in marked)


def test_line_pairs_join_takes_whole_next_word():
    from rapdna.experiments import line_pairs
    line = _line([("git", "ɡˈit"), ("styl", "stˈɨl"), ("pakuję", "pakˈujɛ")])
    joins = {c.text for c in line_pairs.cells(0, line, {}) if c.kind == "join"}
    assert "git styl" in joins and "styl pakuję" not in joins


def test_color_by_key_gap():
    from types import SimpleNamespace as N
    from rapdna.experiments.line_pairs import color_by_key
    cs = [N(key=("a",), line=0), N(key=("e",), line=0), N(key=("a",), line=3), N(key=("a",), line=20)]
    assert color_by_key(cs, gap=8) == [0, 1, 0, 2]


def test_line_pairs_motif_spreads_to_next_line():
    from rapdna.experiments import line_pairs
    a = _line([("masz", "mˈaʃ"), ("mocne", "mˈɔtsnɛ"), ("combo", "kˈɔmbɔ"), ("dzisiaj", "dʑˈiɕaj")])
    b = _line([("mamy", "mˈamɨ"), ("proste", "prˈɔstɛ"), ("motto", "mˈɔttɔ"), ("wszędzie", "fʂˈɛɲdʑɛ")])
    c = _line([("tylko", "tˈɨlkɔ"), ("mokre", "mˈɔkrɛ"), ("drzewa", "dʐˈɛva")])  # o-e like „proste” above
    marked = {(cell.line, cell.text) for cell, _ in line_pairs.mark([a, b, c])}
    assert (2, "mokre") in marked


def test_icc_extremes():
    import numpy as np
    from rapdna.stats.reliability import icc
    g = np.array(["a"] * 5 + ["b"] * 5)
    assert icc(np.array([1.0] * 5 + [9.0] * 5) + np.arange(10) * 0.001, g) > 0.99  # differences only between rappers
    assert icc(np.array([1, 9, 1, 9, 5, 9, 1, 9, 1, 5], float), g) < 0.05  # differences only between songs


def test_vulgar_list_no_false_friends():
    from rapdna.stats.surface import vulgar_re
    v = vulgar_re()
    assert all(v.fullmatch(w) for w in ["kurwa", "chujowy", "zajebisty", "spierdolić", "gówno", "sram"])
    assert not any(v.fullmatch(w) for w in ["przesłuchuje", "wymachuje", "machina", "dupleks", "srebro"])


def test_self_mention_whole_phrase():
    from rapdna.stats.surface import self_re
    r = self_re(["Ten Typ Mes", "Mes"])
    assert r.findall("ten typ mes i ten chłopak, mes. tenis") == ["ten typ mes", "mes"]


def test_phrase_variants():
    from rapdna.stats.surface import _variant
    assert _variant("dziennik pokładowy", "pokładowy europa") and _variant("mam wyjebane", "mam wyjebane na")
    assert not _variant("w moim mieście", "na spokojnie")


def test_vocab_classes_line_start_is_not_proper_name():
    import pandas as pd
    from rapdna.stats.surface import vocab_classes
    rows = [("Ona", 0, "pl"), ("ona", 2, "pl"), ("Rychu", 1, "pl"), ("Rychu", 3, "pl"), ("Dlatego", 0, "pl")]
    w = pd.DataFrame(rows, columns=["form", "w", "lang"]).assign(low=lambda d: d.form.str.lower())
    c = vocab_classes(w)
    assert "rychu" in c["proper_names"] and "ona" not in c["proper_names"] and "dlatego" not in c["proper_names"]
