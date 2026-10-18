from rapdna.text.sections import attributed_to, parse_header, parse_sections

SAMPLE = """[Tekst piosenki "X"]

[Zwrotka 1: Taco Hemingway]
Kto Ty jesteś? Polak mały (Polak mały, Polak mały)
Jaki znak Twój?

[Refren]
Tańczę polskie tango
Nogi w błocie mam

[Zwrotka 2: Taco Hemingway i Łona]
Wspólna linijka

[Refren]
Tańczę polskie tango
Nogi w błocie mam
"""


def test_header_types_and_performers():
    assert parse_header("Zwrotka 1: Taco Hemingway") == ("verse", ["Taco Hemingway"])
    assert parse_header("Verse 2: Quebonafide & Taco Hemingway") == ("verse", ["Quebonafide", "Taco Hemingway"])
    assert parse_header("Przedrefren") == ("prechorus", [])
    assert parse_header("Hook: Mata") == ("chorus", ["Mata"])
    assert parse_header("Outro") == ("outro", [])


def test_parse_sections_solo_song():
    secs = parse_sections(SAMPLE, "Taco Hemingway", featured=[])
    assert [s.type for s in secs] == ["verse", "chorus", "verse", "chorus"]
    assert secs[0].lines[0] == "Kto Ty jesteś? Polak mały"  # ad-lib removed
    assert secs[1].performers == ["Taco Hemingway"]  # no performer header, no guests
    assert [s.is_dup for s in secs] == [False, False, False, True]
    assert attributed_to(secs[0], "Taco Hemingway")
    assert not attributed_to(secs[2], "Taco Hemingway")  # a shared verse


def test_unlabelled_section_with_unlabelled_guest_is_unassigned():
    secs = parse_sections(SAMPLE, "Taco Hemingway", featured=["Łona", "Fisz"])  # Fisz is not credited anywhere
    assert secs[1].performers == []


def test_unlabelled_section_goes_to_primary_when_every_guest_is_labelled():
    secs = parse_sections(SAMPLE, "Taco Hemingway", featured=["Łona"])
    assert secs[1].performers == ["Taco Hemingway"]


def test_unlabelled_dj_guest_does_not_block_primary():
    secs = parse_sections("[Zwrotka 1]\nwers\n\n[Cuty]\nskrecz", "Quebonafide", featured=["DJ Flip"])
    assert secs[0].performers == ["Quebonafide"]


def test_genius_footer_removed_also_when_glued():
    text = "[Zwrotka 1]\nnie pamiętam nicTekst i adnotacje na Rap Genius Polska\nwers drugi\n\n[Tekst - Rap Genius Polska]"
    secs = parse_sections(text, "Eripe", featured=[])
    assert [ln for s in secs for ln in s.lines] == ["nie pamiętam nic", "wers drugi"]


def test_name_only_title_and_group_headers():
    text = "[Utwór 1: TRAWA]\n\n[Zwrotka 1]\nwers\n\n[Mata]\ngadka\n\n[Refren: Mata, Quebonafide, Obaj]\nrazem\n\n[?]\nkto"
    secs = parse_sections(text, "Quebonafide", featured=["Mata"], aliases=["Quebo"])
    assert [s.performers for s in secs] == [["Quebonafide"], ["Mata"], ["Mata", "Quebonafide"], ["?"]]


def test_aliases_and_double_marker():
    secs = parse_sections("[Zwrotka 1: Bałagane]\nwers\n\n[Zwrotka 2: Oxon x2]\nwers drugi", "Kaz Bałagane", ["X"])
    assert attributed_to(secs[0], "Kaz Bałagane", ["Bałagane"])
    assert secs[1].performers == ["Oxon"]
