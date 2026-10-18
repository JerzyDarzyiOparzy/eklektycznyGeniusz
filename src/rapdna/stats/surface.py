"""Surface features from the plan (docs/en/features.md): song structure, producers, vocabulary classes,
self-mentions and favourite phrases. Each is computed per song and per rapper; whether it describes the rapper or the
song is tested in `stats/reliability.py`. Kept out of the comparisons until validated.

Song structure (the whole Genius text, all sections):
- `song_lines`: lines in the song; `chorus_share`: share of lines in choruses (pre- and post-choruses included);
- `guests`: number of guests (Genius); `rapper_share`: share of lines attributed to the rapper;
- `rapper_verses`, `lines_per_verse`: the rapper's verses and their mean length in lines;
- `intro_outro`: whether the song has an intro or an outro.
Producers (Genius metadata, API cache): `producers` (list). Per rapper: distinct producers per 10 songs, share of the
most frequent producer, the top three.
Language (the rapper's lines, without repeats), word classes in `vocab_classes`:
- `vulgarisms_1000`: words matching `config/vulgarisms.yaml`, per 1000 words;
- `slang_1000`: words from Słownik Miejski (English ones too: „flow”, „hype”) that are not in the general dictionary;
- `out_of_dictionary_1000`: Polish words in no dictionary (coinages, slang missing from Miejski, loans with a Polish
  ending, typos); a raw measure until `data/candidates/words_to_review.csv` is reviewed;
- proper names are not counted as slang; collected in `data/candidates/proper_names.csv` (kind and pronunciation to
  fill in);
- `self_mentions_1000`: the rapper's own name (with aliases) per 1000 words.
Favourite phrases (examples only, not a number): runs of 2–4 words (not only function words) in ≥ MIN_SONGS of the
rapper's songs, ordered by lift over the rest of the corpus (share of the rapper's songs / share of other songs).

Usage: python -m rapdna.stats.surface → data/stats/surface_features.csv (rappers), surface_features_songs.parquet,
phrases.csv
"""
import json
import re
from collections import Counter, defaultdict

import pandas as pd
import yaml

from rapdna import paths
from rapdna.genius.api import CACHE
from rapdna.ingest import load_config, load_songs
from rapdna.text.nlp import is_function_word

STATS = paths.DATA / "stats"
CANDIDATES = paths.DATA / "candidates"
CHORUS = {"chorus", "prechorus", "postchorus"}
MIN_SONGS = 3
NGRAMS = (2, 3, 4)
GENERAL_ZIPF = 4.0  # a word frequent in general Polish (wordfreq) is not slang, even when it is in Miejski („pod”)
ENGLISH_ZIPF = 5.0  # a very frequent English word („yeah”, „here”, „last”) is not slang; „flow”, „cash”, „hype” are
UNKNOWN_ZIPF = 1.5  # a word almost unknown to general Polish (wordfreq): a coinage candidate


def vulgar_re() -> re.Pattern:
    d = yaml.safe_load((paths.CONFIG / "vulgarisms.yaml").read_text(encoding="utf-8"))
    return re.compile("|".join(f"(?:{p})" for p in d["polish"] + d["english"]))


def vocab_classes(words: pd.DataFrame) -> dict[str, set[str]]:
    """Classes of word forms (lower case) in the rappers' lines:
    - `slang`: one-word entries of Słownik Miejski, English ones too („flow”, „hype”), without words from the general
      dictionary or frequent in general Polish (the general dictionary has gaps: „pod”, „czego”), no function words;
    - `out_of_dictionary`: Polish forms outside the general dictionary and almost unknown to wordfreq, not slang from
      Miejski: coinages („śmiechulec”, „wódzina”), slang missing from Miejski, loans with a Polish ending („flexuję”),
      but also typos; to be separated by a language model (`data/candidates/words_to_review.csv`);
    - `proper_names`: forms usually capitalised (nicknames, first names, brands, places); not counted as slang,
      collected for review and pronunciation fixes (`data/candidates/proper_names.csv`)."""
    from wordfreq import zipf_frequency

    forms = set(words.low[words.low.str.fullmatch(r"[a-ząćęłńóśźż]{3,}")])
    known = set(pd.read_parquet(paths.PHONETIC_DICT, columns=["word"], filters=[("word", "in", sorted(forms))]).word)
    # a capital letter counts only inside the line (every Genius line starts with one: „Ona”, „Dlatego”)
    mid = words[words.low.isin(forms) & (words.w > 0)]
    cap = mid.groupby("low").form.agg(lambda f: f.str[:1].str.isupper().mean())
    proper = set(cap[cap > 0.5].index)
    lang = words.groupby("low").lang.agg(lambda x: x.mode().iloc[0])
    sl = pd.read_csv(paths.SLANG, usecols=["word"]).word.dropna().str.strip().str.lower()
    slang = set()
    for x in set(sl) & forms - known - proper:
        if is_function_word(x):
            continue
        if lang.get(x) == "en":
            if zipf_frequency(x, "en") < ENGLISH_ZIPF:
                slang.add(x)
        elif zipf_frequency(x, "pl") < GENERAL_ZIPF:
            slang.add(x)
    unknown = {x for x in forms - known - proper - slang
               if len(x) >= 4 and lang.get(x) == "pl" and zipf_frequency(x, "pl") < UNKNOWN_ZIPF}
    return {"slang": slang, "out_of_dictionary": unknown, "proper_names": proper}


def export_candidates(words: pd.DataFrame, lines: pd.DataFrame, classes: dict[str, set[str]]) -> None:
    """Lists for a later review by a language model: out-of-dictionary words (category to fill in: coinage / slang /
    loan / diminutive / typo / correct word) and proper names (kind + corrected pronunciation)."""
    CANDIDATES.mkdir(parents=True, exist_ok=True)
    text = lines.set_index("line_uid").text
    for name, forms, extra in (("words_to_review", classes["out_of_dictionary"] | classes["slang"], ["category"]),
                               ("proper_names", classes["proper_names"], ["kind", "fixed_pronunciation"])):
        w = words[words.low.isin(forms)]
        g = w.groupby("low").agg(form=("form", lambda f: f.mode().iloc[0]), count=("form", "size"),
                                 rappers=("artist", lambda a: "; ".join(sorted(set(a)))),
                                 ipa=("ipa", "first"), language=("lang", "first"), example=("line_uid", "first"))
        g.index.name = "lower"
        g["example"] = g.example.map(text)
        if name == "words_to_review":
            g["in_miejski"] = g.index.isin(classes["slang"])
        for col in extra:
            g[col] = ""
        g.sort_values("count", ascending=False).to_csv(CANDIDATES / f"{name}.csv")


def self_re(names: list[str]) -> re.Pattern:
    """The rapper's own name as a whole phrase („ten typ mes”, not every „ten”)."""
    alts = sorted({n.lower() for n in names}, key=len, reverse=True)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(a) for a in alts) + r")(?!\w)")


def producers(song_id: int) -> list[str]:
    f = CACHE / f"songs_{song_id}_text_format-plain.json"
    if not f.exists():
        return []
    return [p["name"] for p in json.loads(f.read_text(encoding="utf-8"))["song"].get("producer_artists", [])]


def song_table(log=print) -> tuple[pd.DataFrame, dict]:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["line_uid", "w", "form", "lang", "ipa"])
    own = lines[lines.attributed & ~lines.is_dup]
    words = words.merge(own[["line_uid", "song_id", "artist", "section", "line"]], on="line_uid")
    words["low"] = words.form.str.lower()
    featured = {s["song_id"]: s["featured"] for s in load_songs()}
    selfs = {a["name"]: self_re([a["name"], *a.get("aliases", [])]) for a in load_config()["artists"]}
    texts = own.groupby("song_id").text.agg(lambda t: " ".join(t).lower())
    vre, classes = vulgar_re(), vocab_classes(words)
    export_candidates(words, own, classes)
    words["vulgar"] = words.low.map(lambda w: bool(vre.fullmatch(w)))
    words["slang"] = words.low.isin(classes["slang"])
    words["unknown"] = words.low.isin(classes["out_of_dictionary"])
    rows = []
    for sid, ln in lines.groupby("song_id"):
        artist = ln.artist.iloc[0]
        sec = ln.groupby("section").agg(kind=("section_type", "first"), n=("line", "size"),
                                        own=("attributed", "any"))
        verses = sec[(sec.kind == "verse") & sec.own]
        wd = words[words.song_id == sid]
        n = max(len(wd), 1)
        rows.append({"song_id": sid, "artist": artist, "year": ln.year.iloc[0], "album": ln.album.iloc[0],
                     "song_lines": len(ln), "chorus_share": ln.section_type.isin(CHORUS).mean(),
                     "guests": len(featured.get(sid, [])), "rapper_share": ln.attributed.mean(),
                     "rapper_verses": len(verses), "lines_per_verse": verses.n.mean() if len(verses) else None,
                     "intro_outro": bool(sec.kind.isin({"intro", "outro"}).any()),
                     "rapper_words": len(wd), "vulgarisms_1000": 1000 * wd.vulgar.sum() / n,
                     "slang_1000": 1000 * wd.slang.sum() / n, "out_of_dictionary_1000": 1000 * wd.unknown.sum() / n,
                     "self_mentions_1000": (1000 * len(selfs[artist].findall(texts.get(sid, ""))) / n
                                            if artist in selfs else 0.0),
                     "producers": producers(sid)})
    log(f"songs: {len(rows)}; forms: slang {len(classes['slang'])}, out of dictionary "
        f"{len(classes['out_of_dictionary'])}, proper names {len(classes['proper_names'])}")
    return pd.DataFrame(rows), {"classes": classes, "words": words}


def artist_table(songs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for artist, g in songs.groupby("artist"):
        prod = Counter(p for ps in g.producers for p in ps)
        with_prod = sum(bool(ps) for ps in g.producers)
        top = prod.most_common(3)
        w = g.rapper_words.sum()
        rows.append({"artist": artist, "songs": len(g),
                     "song_lines": g.song_lines.median(), "chorus_share": g.chorus_share.mean(),
                     "guests_per_song": g.guests.mean(), "songs_with_guests": (g.guests > 0).mean(),
                     "rapper_share": g.rapper_share.mean(), "lines_per_verse": g.lines_per_verse.median(),
                     "intro_outro": g.intro_outro.mean(),
                     # weighted by the rapper's words, like the features computed over the whole catalogue
                     "vulgarisms_1000": (g.vulgarisms_1000 * g.rapper_words).sum() / w,
                     "slang_1000": (g.slang_1000 * g.rapper_words).sum() / w,
                     "out_of_dictionary_1000": (g.out_of_dictionary_1000 * g.rapper_words).sum() / w,
                     "self_mentions_1000": (g.self_mentions_1000 * g.rapper_words).sum() / w,
                     "producers_per_10_songs": 10 * len(prod) / max(with_prod, 1),
                     "main_producer_share": top[0][1] / with_prod if top else None,
                     "main_producers": "; ".join(f"{p} ({n})" for p, n in top),
                     "songs_with_producer": with_prod / len(g)})
    return pd.DataFrame(rows)


def _variant(a: str, b: str) -> bool:
    """The same phrase in another form: one contains the other or they share a word that is not a function word."""
    return a in b or b in a or any(not is_function_word(t) for t in set(a.split()) & set(b.split()))


def phrases(words: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """The rappers' favourite phrases: n-grams in ≥ MIN_SONGS of the rapper's songs, rare in others."""
    songs_of = defaultdict(set)  # (artist, ngram) → songs
    n_songs = words.groupby("artist").song_id.nunique()
    w = words.sort_values(["song_id", "section", "line", "w"])
    for (artist, sid, _, _), ln in w.groupby(["artist", "song_id", "section", "line"], sort=False):
        toks = list(ln.low)
        for n in NGRAMS:
            for i in range(len(toks) - n + 1):
                g = tuple(toks[i:i + n])
                if all(is_function_word(t) for t in g) or any(len(t) == 1 and not is_function_word(t) for t in g):
                    continue  # only function words, or a spelled-out name („d a b”)
                songs_of[(artist, g)].add(sid)
    by_gram = defaultdict(dict)
    for (artist, g), s in songs_of.items():
        by_gram[g][artist] = len(s)
    rows = []
    total = n_songs.sum()
    for (artist, g), s in songs_of.items():
        k = len(s)
        if k < MIN_SONGS:
            continue
        others = sum(v for a, v in by_gram[g].items() if a != artist)
        share = k / n_songs[artist]
        share_o = (others + 1) / (total - n_songs[artist])
        rows.append({"artist": artist, "phrase": " ".join(g), "songs": k, "song_share": round(share, 3),
                     "other_songs": others, "lift": round(share / share_o, 1)})
    df = pd.DataFrame(rows).sort_values(["artist", "lift", "songs"], ascending=[True, False, False])
    out = []
    for _, g in df.groupby("artist"):
        kept = []
        for r in g.itertuples():
            if any(_variant(r.phrase, k.phrase) and abs(r.songs - k.songs) <= 2 for k in kept):
                continue  # a variant of the same phrase („dziennik pokładowy” / „pokładowy europa”)
            kept.append(r)
            if len(kept) == top:
                break
        out += [r._asdict() for r in kept]
    return pd.DataFrame(out).drop(columns="Index")


def run(log=print):
    STATS.mkdir(parents=True, exist_ok=True)
    songs, aux = song_table(log)
    songs.to_parquet(STATS / "surface_features_songs.parquet", index=False)
    art = artist_table(songs)
    art.to_csv(STATS / "surface_features.csv", index=False)
    ph = phrases(aux["words"])
    ph.to_csv(STATS / "phrases.csv", index=False)
    return songs, art, ph, aux


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    songs, art, ph, aux = run()
    print(art.drop(columns=["main_producers"]).round(2).to_string(index=False))
    print(art[["artist", "main_producers"]].to_string(index=False))
    for a, g in ph.groupby("artist"):
        print(a, "|", ", ".join(f"{r.phrase} ({r.songs})" for r in g.head(6).itertuples()))
