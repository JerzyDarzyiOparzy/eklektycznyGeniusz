"""Word → IPA. Sources in order: exception list → phonetic dictionary (1.79 M forms) → espeak-ng (Polish, or English
for English words), with an on-disk cache. Which language a word is read in follows config/word_language.yaml."""
import json
import re
import subprocess
from pathlib import Path

import pandas as pd
import yaml
from num2words import num2words
from wordfreq import zipf_frequency

from rapdna import paths
from rapdna.rhymes.patterns import SECONDARY, STRESS

ESPEAK_CACHE = paths.DATA / "espeak_cache.json"
EXCEPTIONS = paths.CONFIG / "pronunciation_exceptions.yaml"

# English espeak phonemes → the closest Polish ones (the way a Polish rapper usually says them).
# American ɑː before r is „a” („car”, „star”); without r it depends on spelling (_en_to_pl). ɜː in en-us always comes
# with r („surfer”, „bird”), and ɚɹ is a single „er” („Wolverine”). Polish rappers shorten the diphthong oʊ to „o”
# („stons”, „hol”, „roling”, heard in recordings, config/heard_pronunciation.yaml), but keep ej and aj
# („łejw”, „dizajn”).
_EN_TO_PL = [
    ("ɑːɹ", "ar"), ("ɑɹ", "ar"), ("ɚɹ", "ɛr"), ("ɜːɹ", "ɛr"), ("ɜː", "ɛr"),
    ("aɪə", "ajɛ"), ("eɪ", "ɛj"), ("aɪ", "aj"), ("ɔɪ", "ɔj"), ("aʊ", "aw"), ("oʊ", "ɔ"), ("əʊ", "ɔ"),
    ("ɪə", "iɛ"), ("eə", "ɛ"), ("ʊə", "uɛ"), ("ɚ", "ɛr"), ("ɝ", "ɛr"), ("iː", "i"),
    ("uː", "u"), ("ɔː", "ɔ"), ("ɑː", "a"), ("ə", "ɛ"), ("ɪ", "i"), ("æ", "ɛ"), ("ʌ", "a"), ("ɑ", "a"),
    ("ɒ", "ɔ"), ("ʊ", "u"), ("ᵻ", "i"), ("ɐ", "a"), ("e", "ɛ"), ("o", "ɔ"), ("θ", "f"), ("ð", "d"),
    ("ɹ", "r"), ("ɾ", "t"), ("h", "x"), ("ʔ", ""), ("ː", ""), ("ɬ", "l"),
]
_FOREIGN = ("es", "it", "fr", "de", "pt")


def _en_to_pl(ipa: str, word: str = "") -> str:
    """Spelling decides two vowels: American ɑ is „o” in words spelled with „o” („Scott”, „rock”) and „a” elsewhere
    („Sinatra”); a final ə written as „a” is „a” („flava”, „Mufasa”)."""
    w = word.lower()
    if "o" in w:
        ipa = re.sub("ɑː?(?![ːɹ])", "ɔ", ipa)
    if w.endswith("a") and ipa.rstrip().endswith("ə"):
        ipa = ipa.rstrip()[:-1] + "a"
    for src, dst in _EN_TO_PL:
        ipa = ipa.replace(src, dst)
    return re.sub("r+", "r", ipa)


def _espeak_word(word: str, voice: str) -> str:
    """One word through stdin (UTF-8). One word per call, because in batches espeak can join neighbouring lines and
    read a full stop aloud („brajdak kropka u”)."""
    out = subprocess.run(
        ["espeak-ng", "-v", voice, "-q", "--ipa", "-b", "1", "--stdin"],
        input=(word + "\n").encode("utf-8"), capture_output=True, check=True,
    ).stdout.decode("utf-8")
    return " ".join(out.split())


def run_espeak(words: list[str], voice: str, workers: int = 8) -> list[str]:
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda w: _espeak_word(w, voice), words))


def _load_lang() -> dict:
    d = yaml.safe_load((paths.CONFIG / "word_language.yaml").read_text(encoding="utf-8"))
    d["always_polish"] = {w.lower() for w in d.get("always_polish") or []}
    d["always_english"] = {w.lower() for w in d.get("always_english") or []}
    return d


LANG = _load_lang()


def mostly_english(word: str, min_en: float) -> bool:
    """English frequency higher than Polish and than each language in _FOREIGN. Names and proper nouns are frequent
    in many languages; „Valentino”, „Cantona”, „Agata” win elsewhere and stay Polish."""
    w = word.lower()
    en, pl = zipf_frequency(w, "en"), zipf_frequency(w, "pl")
    # words very frequent in Polish („by”, „my”, „one”): the plWordNet dictionary lacks pronouns and conjunctions
    return (w not in LANG["always_polish"] and en >= min_en and en > pl and pl < LANG["c_max_pl"]
            and all(en > zipf_frequency(w, lang) for lang in _FOREIGN))


# letters and clusters absent from native Polish spelling (q, x, v, „th”, „ck”, „ee”, doubled consonants, a silent
# final „e”, „c” before a/o/u). Names without them („Toronto”, „Antoni”, „Isla”) a Polish rapper reads in Polish.
_EN_SPELLING = re.compile(
    r"[qxvw]|th|sh|ph|gh|wr|ck|ee|oo|ea|oa|ou|ay|ey|oy|aw|ew|ow|tion|([bdfgklmnprstz])\1"
    r"|[^aeiouy]e$|[^aeiou]y$|c(?![hiez])|^j[aeiouy]"
)


def english_spelling(word: str) -> bool:
    return bool(_EN_SPELLING.search(word.lower()))


def is_english(word: str, in_polish_dict: bool) -> bool:
    """Rule C: a word missing from the Polish dictionary, with English spelling, where English dominates
    (mostly_english). The Polish web is full of English names („steve”, „scott”), so English only has to win."""
    if in_polish_dict:
        return False
    en, pl = zipf_frequency(word, "en"), zipf_frequency(word, "pl")
    clearly_english = en >= 3.0 and en > pl + 1  # „guys”, „skill”, „I'm”
    return clearly_english or english_spelling(word) and mostly_english(word, LANG["c_min_en"])


def is_english_line(tokens: list[str], min_tokens: int = 3, min_share: float = 0.6) -> bool:
    """A line mostly in English: short words shared by both languages („do”, „are”) are then read in English."""
    words = [t.lower() for t in tokens if not t.isdigit()]
    if len(words) < min_tokens:
        return False
    en = sum(zipf_frequency(w, "en") >= 2.5 and zipf_frequency(w, "en") > zipf_frequency(w, "pl") for w in words)
    return en / len(words) >= min_share


def english_loan(word: str) -> bool:
    """Rule A: a word from the Polish dictionary that is read in English in a Polish line."""
    w = word.lower()
    if w in LANG["always_english"]:
        return True
    if w in LANG["always_polish"] or len(w) <= 2:
        return False
    en, pl = zipf_frequency(w, "en"), zipf_frequency(w, "pl")
    return en >= LANG["a_min_en"] and en > pl + LANG["a_margin"] and pl < LANG["a_max_pl"]


# Polish endings after an English stem („shotgun-em”, „Punisher-em”, „joint-ów”), longest first
_PL_SUFFIX_IPA = [
    ("ami", "ami"), ("ach", "ax"), ("owi", "ɔvi"), ("ów", "uf"), ("om", "ɔm"), ("em", "ɛm"), ("ie", "ʲɛ"),
    ("ą", "ɔ̃"), ("ę", "ɛ"), ("a", "a"), ("u", "u"), ("y", "ɨ"), ("i", "i"), ("e", "ɛ"), ("m", "ɛm"),
]
_PL_VOWELS = set("aɛiɔuɨ")


def _english_word(w: str, min_len: int = 4, spelling: bool = True) -> bool:
    """Stem of a hybrid: an English word („shotgun”) or a compound of two English words of ≥ 4 letters each
    („ghost” + „rider”). Shorter stems produced false hybrids („dle” + „a” from „dla”)."""
    if len(w) < min_len or w in LANG["always_polish"] or spelling and not english_spelling(w):
        return False
    if mostly_english(w, LANG["c_min_en"]):
        return True
    return any(mostly_english(w[:i], LANG["h_min_part"]) and mostly_english(w[i:], LANG["h_min_part"])
               for i in range(4, len(w) - 3))


def english_stem(word: str) -> tuple[str, str] | None:
    """Rule H: an English stem with a Polish ending. Returns (stem, IPA of the ending) or None.
    After an apostrophe the ending is explicit („wave'm”, „Steve'a”) and the stem need not have English spelling;
    without one, before „-em” we also try the stem with a silent „e” („Wolverin-em” → „wolverine”)."""
    w = word.lower().replace("’", "'")
    if "'" in w:
        stem, _, suf = w.partition("'")
        sfx = dict(_PL_SUFFIX_IPA).get(suf)
        return (stem, sfx) if sfx and _english_word(stem, min_len=3, spelling=False) else None
    if zipf_frequency(w, "pl") >= LANG["h_max_pl"]:  # an ordinary Polish word missing from the dictionary („tobie”)
        return None
    for suf, sfx in _PL_SUFFIX_IPA:
        if suf == "m" or not w.endswith(suf):
            continue
        base = w[: -len(suf)]
        for stem in (base, base + "e") if suf == "em" else (base,):
            if _english_word(stem):
                return stem, sfx
    return None


def penultimate_stress(ipa: str) -> str:
    """Polish stress on the penultimate syllable (hybrids inflected the Polish way: „szotˈganem”)."""
    ipa = ipa.replace(STRESS, "").replace(SECONDARY, "")
    idx = [i for i, ch in enumerate(ipa) if ch in _PL_VOWELS]
    if not idx:
        return ipa
    i = idx[-2] if len(idx) >= 2 else idx[-1]
    return ipa[:i] + STRESS + ipa[i:]


def context_english(forms: list[str], is_en: list[bool]) -> list[bool]:
    """Line context. Rule D: a word shared by both languages („be”, „not”) next to an English one, when it is clearly
    more frequent in English. Rule E: a word between two English ones („not a player”). Rule N: a run of ≥ 2
    capitalised words with an English member is a proper name („Frank Castle”, „Silver Surfer”)."""
    out = list(is_en)
    low = [f.lower() for f in forms]
    en = [zipf_frequency(w, "en") for w in low]
    pl = [zipf_frequency(w, "pl") for w in low]
    keep_pl = [w in LANG["always_polish"] or polish_in_english_line(w) for w in low]
    changed = True
    while changed:
        changed = False
        for i in range(len(forms)):
            if out[i] or keep_pl[i]:
                continue
            left, right = i > 0 and out[i - 1], i + 1 < len(forms) and out[i + 1]
            d = (left or right) and en[i] >= LANG["d_min_en"] and en[i] > pl[i] + 2 * LANG["a_margin"]
            e = left and right and en[i] >= LANG["e_min_en"] and en[i] >= pl[i]
            if d or e:
                out[i] = changed = True
    i = 0
    while i < len(forms):
        j = i
        while j < len(forms) and forms[j][:1].isupper():
            j += 1
        if j - i >= 2 and any(out[i:j]):
            for k in range(i, j):
                if (not keep_pl[k] and en[k] >= LANG["n_min_en"] and en[k] >= pl[k] - LANG["a_margin"]
                        and all(en[k] > zipf_frequency(low[k], lang) for lang in _FOREIGN)):
                    out[k] = True
        i = max(j, i + 1)
    return out


def polish_in_english_line(word: str) -> bool:
    """Rule B: a Polish word in an English line is read in Polish („jej”, „że”, „żaden”)."""
    w = word.lower()
    return zipf_frequency(w, "en") < LANG["b_max_en"] and zipf_frequency(w, "pl") >= LANG["b_min_pl"]


# Polish letter names for acronyms read letter by letter („WKU” → wu-ka-u, stress on the last letter)
LETTERS = {"a": "a", "b": "bɛ", "c": "tsɛ", "d": "dɛ", "e": "ɛ", "f": "ɛf", "g": "ɡʲɛ", "h": "xa", "i": "i",
           "j": "jɔt", "k": "ka", "l": "ɛl", "ł": "ɛw", "m": "ɛm", "n": "ɛn", "o": "ɔ", "p": "pɛ", "q": "ku", "r": "ɛr",
           "s": "ɛs", "t": "tɛ", "u": "u", "v": "fau", "w": "vu", "x": "iks", "y": "iɡrɛk", "z": "zɛt", "ś": "ɛɕ",
           "ź": "ʑɛt", "ż": "ʒɛt", "ć": "tɕɛ", "ń": "ɛɲ", "ó": "u"}
_VOWEL_LETTERS = set("aeiouyąęó")


def spelled_acronym(token: str) -> str | None:
    """IPA of an acronym read letter by letter („WKU” rhymes on „u”). Read letter by letter:
    2–5 capital letters that cannot be read as a word: no vowel, or two consonants at the start („SB”, „PRL”,
    „WKU”, „DNA”). „UFO”, „PIN”, „VIP” are read as words."""
    if not (2 <= len(token) <= 5 and token.isalpha() and token.isupper()):
        return None
    low = token.lower()
    if any(ch in _VOWEL_LETTERS for ch in low) and not (low[0] not in _VOWEL_LETTERS and low[1] not in _VOWEL_LETTERS):
        return None
    names = [LETTERS.get(ch) for ch in low]
    if None in names:
        return None
    return "".join(names[:-1]) + STRESS + names[-1]


def number_to_words(token: str) -> str:
    return num2words(int(token), lang="pl")


class Lexicon:
    """Pronunciation dictionary for the corpus vocabulary. Loads only the words it needs."""

    def __init__(self):
        self.ipa: dict[str, str] = {}
        self.lemma: dict[str, str] = {}
        self.lang: dict[str, str] = {}
        self.source: dict[str, str] = {}  # dict | exception | espeak
        self.ipa_en: dict[str, str] = {}
        self.exceptions = self._load_exceptions()
        self.cache = json.loads(ESPEAK_CACHE.read_text(encoding="utf-8")) if ESPEAK_CACHE.exists() else {}

    @staticmethod
    def _load_exceptions() -> dict[str, str]:
        if not EXCEPTIONS.exists():
            return {}
        return {k.lower(): v for k, v in (yaml.safe_load(EXCEPTIONS.read_text(encoding="utf-8")) or {}).items()}

    def load(self, vocab: set[str]) -> None:
        vocab = {w.lower() for w in vocab} - set(self.ipa)
        if not vocab:
            return
        df = pd.read_parquet(paths.PHONETIC_DICT, filters=[("word", "in", sorted(vocab))])
        for row in df.itertuples():
            self.ipa.setdefault(row.word, row.ipa)
            self.lemma.setdefault(row.word, row.lemma)
            self.lang.setdefault(row.word, "pl")
            self.source.setdefault(row.word, "dict")
        for w, ipa in self.exceptions.items():
            if w in vocab:
                self.ipa[w], self.lang[w], self.source[w] = ipa, "pl", "exception"

        missing = sorted(vocab - set(self.ipa))
        ru = [w for w in missing if _CYRILLIC.search(w)]
        en = [w for w in missing if w not in set(ru) and is_english(w, False)]
        # rule A: English words that are also in the Polish dictionary („beat”, „trap”)
        en += [w for w in vocab - set(missing) if self.source.get(w) == "dict" and english_loan(w)]
        en += [w for w in missing if w not in set(en) | set(ru) and w in LANG["always_english"]]
        # rule H: English stem with a Polish ending („shotgunem”, „wave'm”): stem in English, ending in Polish
        hyb = {w: st for w in missing if w not in set(en) | set(ru) and (st := english_stem(w))}
        stems = sorted({st for st, _ in hyb.values() if f"en-us:{st}" not in self.cache})
        for st, ipa in zip(stems, run_espeak(stems, "en-us")):
            self.cache[f"en-us:{st}"] = ipa
        for w, (st, sfx) in hyb.items():
            self.ipa[w] = penultimate_stress(_en_to_pl(self.cache[f"en-us:{st}"], st) + sfx)
            self.lang[w], self.source[w] = "en", "espeak"
        pl = [w for w in missing if w not in set(en) | set(ru) | set(hyb)]
        for words, voice, lang in ((pl, "pl", "pl"), (en, "en-us", "en"), (ru, "ru", "ru")):
            todo = [w for w in words if f"{voice}:{w}" not in self.cache]
            for w, ipa in zip(todo, run_espeak(todo, voice)):
                self.cache[f"{voice}:{w}"] = ipa
            for w in words:
                ipa = self.cache[f"{voice}:{w}"]
                self.ipa[w] = _en_to_pl(ipa, w) if lang == "en" else ipa
                self.lang[w] = lang
                self.source[w] = "espeak"
        if missing:
            ESPEAK_CACHE.parent.mkdir(parents=True, exist_ok=True)
            ESPEAK_CACHE.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")

    def load_english(self, vocab: set[str]) -> None:
        """English pronunciation (mapped to Polish phonemes) for the words of English lines."""
        vocab = {w.lower() for w in vocab}
        todo = sorted(w for w in vocab if f"en-us:{w}" not in self.cache)
        for w, ipa in zip(todo, run_espeak(todo, "en-us")):
            self.cache[f"en-us:{w}"] = ipa
        self.ipa_en.update({w: _en_to_pl(self.cache[f"en-us:{w}"], w) for w in vocab})
        if todo:
            ESPEAK_CACHE.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")

    def __getitem__(self, word: str) -> str:
        return self.ipa.get(word.lower(), "")


WORD_RE = re.compile(r"[^\W\d_]+(?:['’-][^\W\d_]+)*|\d+", re.UNICODE)

# Cyrillic letters that look Latin (they turn up in Genius lyrics)
_LATIN = re.compile(r"[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
_HOMOGLYPHS = str.maketrans("аеорсухіАЕОРСХКМТВН", "aeopcyxiAEOPCXKMTBH")


def tokenize(line: str) -> list[str]:
    """Words of a line; numbers spelled out („2” → „dwa”)."""
    out = []
    for tok in WORD_RE.findall(line):
        if _LATIN.search(tok):  # „dobrzе” with a Cyrillic „е” → Latin; fully Russian words stay
            tok = tok.translate(_HOMOGLYPHS)
        out.extend(number_to_words(tok).split() if tok.isdigit() else [tok])
    return out


def build_dictionary_parquet(src: Path, dst: Path) -> int:
    """plwordnet_phonetic_dict.csv → parquet (word in lower case, lemma, ipa)."""
    df = pd.read_csv(src, dtype=str, keep_default_na=False)
    df["word"] = df["word"].str.lower()
    df = df[df["ipa"].str.len() > 0].drop_duplicates(["word", "lemma"]).sort_values("word")
    df.to_parquet(dst, index=False, row_group_size=100_000)
    return len(df)
