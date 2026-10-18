from rapdna.figures.repetition import is_anaphora, is_epiphora
from rapdna.figures.sound import find_alliterations


def w(form, ipa, fn=False):
    return (form, form, ipa, fn)


def test_alliteration_skips_function_words():
    line = [w("pieniądze", "pʲɛɲˈɔndzɛ"), w("w", "f", True), w("portfelu", "pɔrtfˈɛlu"), w("pękają", "pɛŋkˈajɔ̃")]
    found = find_alliterations(line)
    assert len(found) == 1 and found[0].words == [0, 2, 3]


def test_no_alliteration_from_prepositions():
    line = [w("w", "f", True), w("domu", "dˈɔmu"), w("w", "f", True), w("lesie", "lˈɛɕɛ"), w("w", "f", True)]
    assert find_alliterations(line) == []


def test_anaphora_and_epiphora():
    assert is_anaphora(["nie", "mam", "czasu"], ["nie", "mam", "hajsu"])
    assert not is_anaphora(["i", "idę"], ["i", "wracam"])
    assert is_anaphora(["i", "znowu", "to"], ["i", "znowu", "tamto"])
    assert not is_anaphora(["to", "samo"], ["to", "samo"])  # a repeated line
    assert is_epiphora(["tańczę", "polskie", "tango"], ["gram", "w", "tango"])


def test_echo_and_adlibs_are_not_figures():
    assert not is_epiphora(["narazie", "muszę", "tutaj", "swoje", "zgarnąć"], ["swoje", "zgarnąć"])
    assert not is_epiphora(["strzały", "ej"], ["a", "miały", "być", "strzały", "ej"])
    assert not is_anaphora(["byłem", "na", "dnie", "już", "tam", "nie", "wrócę", "nie"],
                           ["byłem", "na", "dnie", "już", "tam", "nie", "wrócę"])
    assert not is_anaphora(["ej", "ej"], ["ej"])
    assert is_epiphora(["wtedy", "słyszę", "ryk", "drzew", "witaj", "w", "hotelu", "marmur"],
                       ["nagle", "słyszę", "krzyk", "mew", "witaj", "w", "hotelu", "marmur"])
