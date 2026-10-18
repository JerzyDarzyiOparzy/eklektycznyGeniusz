"""Sound figures within a line (plan, phase 3): alliteration, assonance and consonance chains, onomatopoeia.

All are counted on content words (prepositions, conjunctions, pronouns and interjections are skipped and do not break
a run), and at least two different lemmas are required, so that repeating one word does not pass for a figure.
- alliteration: ≥ `min_run` consecutive words start with the same consonant;
- assonance chain: ≥ `min_run` consecutive words have the same stressed vowel;
- consonance chain: ≥ `min_run` consecutive words have the same consonants after the stressed vowel (coda + onset of
  the next syllable, e.g. „-st-”: kostka, chustka, pustka);
- onomatopoeia: a word from the sound-imitation list (without ambiguous words like „tak”, „hop”) or a short
  out-of-dictionary word repeated („wrum wrum”).
"""
from dataclasses import dataclass

from rapdna.figures.repetition import INTERJECTIONS
from rapdna.phonology.syllables import stressed_index, syllabify
from rapdna.rhymes.patterns import phonemes, vowels

ONOMATOPOEIA = set("""
bum bam bang pif paf puf puk stuk łup trach brzdęk dzyń ding dong tik tyk plask chlast
chlup bęc pstryk klik klak bzz bzzz wrum brum ziuu fiu szast prask trzask cyk ciach
ratata ratatata pow bam blam blah bla bang skrrt skrr skrrr brrr brr grr hau miau kukuryku kwa ćwir gul gulgul
""".split())


@dataclass
class Figure:
    kind: str
    key: str
    words: list[int]  # word indices in the line


def initial_consonant(ipa: str) -> str | None:
    ph = [p for p in phonemes(ipa) if p not in ("ˈ", "ˌ")]
    if not ph or ph[0] in vowels() or ph[0] == "j":
        return None
    return ph[0]


def stressed_vowel(ipa: str) -> str | None:
    s = syllabify(ipa) if ipa else ()
    return s[stressed_index(s)].nucleus if s else None


def post_stress_consonants(ipa: str) -> str | None:
    s = syllabify(ipa) if ipa else ()
    if not s:
        return None
    i = stressed_index(s)
    cons = list(s[i].coda) + (list(s[i + 1].onset) if i + 1 < len(s) else [])
    return "".join(cons) or None


def _runs(content: list[tuple[int, str | None, str]], kind: str, min_run: int) -> list[Figure]:
    out, run = [], []
    for item in content + [(None, None, None)]:
        if run and item[1] is not None and item[1] == run[-1][1]:
            run.append(item)
            continue
        if len(run) >= min_run and len({lem for _, _, lem in run}) >= 2:
            out.append(Figure(kind, run[0][1], [i for i, _, _ in run]))
        run = [item] if item[1] is not None else []
    return out


def _content(words: list[tuple[str, str, str, bool]]):
    return [(i, form, lemma, ipa) for i, (form, lemma, ipa, fn) in enumerate(words)
            if not fn and len(form) >= 2 and form.lower() not in INTERJECTIONS]


def find_alliterations(words: list[tuple[str, str, str, bool]], min_run: int = 3) -> list[Figure]:
    """words: (form, lemma, ipa, function) for every word of the line."""
    return _runs([(i, initial_consonant(ipa), lem) for i, _, lem, ipa in _content(words)], "alliteration", min_run)


def find_assonance_chains(words, min_run: int = 3) -> list[Figure]:
    return _runs([(i, stressed_vowel(ipa), lem) for i, _, lem, ipa in _content(words)], "assonance_chain", min_run)


def find_consonance_chains(words, min_run: int = 3) -> list[Figure]:
    return _runs([(i, post_stress_consonants(ipa), lem) for i, _, lem, ipa in _content(words)],
                 "consonance_chain", min_run)


def find_onomatopoeia(words: list[tuple[str, str, str, bool]], in_dict: set[str] | None = None) -> list[Figure]:
    out = []
    forms = [w[0].lower() for w in words]
    for i, f in enumerate(forms):
        reduplicated = (i + 1 < len(forms) and forms[i + 1] == f) or (i and forms[i - 1] == f)
        unknown = in_dict is not None and f not in in_dict
        if f in ONOMATOPOEIA or (reduplicated and len(f) <= 5 and unknown and f not in INTERJECTIONS):
            out.append(Figure("onomatopoeia", f, [i]))
    return out
