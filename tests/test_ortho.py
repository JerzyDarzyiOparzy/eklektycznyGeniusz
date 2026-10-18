from rapdna.text.ortho import syllables


def test_syllables():
    assert syllables("tango", 2) == ["tan", "go"]
    assert syllables("siano", 2) == ["sia", "no"]
    assert syllables("kosztować", 3) == ["kosz", "to", "wać"]  # both splits are correct; enough for display
    assert syllables("Warszawa", 3) == ["War", "sza", "wa"]
    assert syllables("freestyle", 2) == ["freestyle"]  # English spelling: the nucleus count does not match
    assert syllables("dom", 1) == ["dom"]
