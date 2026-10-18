"""Text features from morphology, frequency lists and the raw lyrics.

All features are computed per song (for the rapper-vs-song reliability check in `stats/reliability.py`) and
aggregated per rapper. Like the other new features they stay out of comparisons until validated.

- tense and mood (spaCy morphology): share of finite verbs in the past, present and future tense, imperatives
  per 100 verbs. Polish has two future forms: the auxiliary „będę” and perfective verbs in present form („zrobię”);
- comparisons per 100 lines: „jak / niczym / jakby / niby / jakoby” followed by a noun, name or adjective;
- diminutives and augmentatives per 1000 words (strong suffixes only: -uś, -unio, -eczek, -iczek, -uszek,
  -eńki, -utki, -ątko, -isko and -ik/-yk on a known base: „hajsik” ← „hajs”);
- rare words: share of Polish words that are rare in general Polish (wordfreq Zipf < 3);
- repetitiveness: compressed / raw size of the rapper's lines in a song (lower = more repetitive);
- ad-libs per 100 lines: parenthesised fragments in the raw Genius lyrics (whole song, guests included);
- collaborations: who appears on whose songs (`data/stats/collaborations.csv`).

Usage: python -m rapdna.stats.textual → data/stats/text_features_songs.parquet, text_features.csv,
adlibs.csv, collaborations.csv
"""
import json
import re
import zlib
from collections import Counter

import pandas as pd

from rapdna import paths
from rapdna.ingest import load_songs
from rapdna.text.nlp import is_function_word

STATS = paths.DATA / "stats"
MORPH_CACHE = paths.DATA / "morph_cache.parquet"
COMPARATIVES = {"jak", "niczym", "jakby", "niby", "jakoby"}
RARE_ZIPF = 3.0
DIMINUTIVE = re.compile(r".{3,}(uś|usia|unio|eczek|eczka|iczek|uszek|eńki|eńka|utki|utka|ątko|isko|uchna)$")
SHORT_DIMINUTIVE = re.compile(r"(.{3,})(ik|yk)$")
ADLIB = re.compile(r"\(([^)]{1,40})\)")
REPEAT_MARK = re.compile(r"^x\d+$|^\d+x$")


def morphology(lines: pd.DataFrame, words: pd.DataFrame, log=print) -> pd.DataFrame:
    """Part of speech and morphology of every word of the rapper's lines (cached by line_uid)."""
    cached = pd.read_parquet(MORPH_CACHE) if MORPH_CACHE.exists() else pd.DataFrame(columns=["line_uid"])
    todo = sorted(set(lines.line_uid) - set(cached.line_uid))
    if todo:
        import spacy
        from spacy.tokens import Doc

        log(f"spaCy morphology: {len(todo)} lines…")
        nlp = spacy.load("pl_core_news_lg", exclude=["parser", "ner"])
        w = words[words.line_uid.isin(todo)].sort_values(["line_uid", "w"])
        groups = [(uid, list(g.form)) for uid, g in w.groupby("line_uid", sort=False)]
        docs = nlp.pipe((Doc(nlp.vocab, words=forms) for _, forms in groups), batch_size=512)
        rows = [{"line_uid": uid, "w": i, "pos": t.pos_, "morph": str(t.morph)}
                for (uid, _), doc in zip(groups, docs) for i, t in enumerate(doc)]
        cached = pd.concat([cached, pd.DataFrame(rows)], ignore_index=True)
        cached.to_parquet(MORPH_CACHE, index=False)
    return cached[cached.line_uid.isin(set(lines.line_uid))]


def tense_counts(m: pd.DataFrame) -> Counter:
    """Past / present / future / imperative counts in one line (rows sorted by word index)."""
    out = Counter()
    fut_aux = False
    for r in m.itertuples():
        if r.pos not in ("VERB", "AUX"):
            continue
        f = dict(x.split("=") for x in r.morph.split("|") if "=" in x)
        if f.get("Mood") == "Imp":
            out["imperative"] += 1
        elif f.get("Tense") == "Fut":
            out["future"] += 1
            fut_aux = True
        elif f.get("Tense") == "Past":
            if not fut_aux:  # „będę pisał” is one future form
                out["past"] += 1
        elif f.get("Tense") == "Pres" and r.pos == "VERB":
            out["future" if f.get("Aspect") == "Perf" else "present"] += 1
    return out


def comparisons(m: pd.DataFrame, forms: list[str]) -> int:
    """„jak / niczym …” followed (within two words) by a noun, name or adjective, not in a question."""
    pos = list(m.pos)
    n = 0
    for i, f in enumerate(forms):
        low = f.lower()
        if low not in COMPARATIVES or i + 1 >= len(forms):
            continue
        if low == "jak" and (i == 0 or forms[-1].endswith("?")):
            continue  # „Jak to?”: a question, not comparison
        if any(p in ("NOUN", "PROPN", "ADJ") for p in pos[i + 1:i + 3]):
            n += 1
    return n


def is_diminutive(word: str, known: set[str]) -> bool:
    if DIMINUTIVE.fullmatch(word):
        return True
    m = SHORT_DIMINUTIVE.fullmatch(word)
    return bool(m and m.group(1) in known)  # „hajsik” ← „hajs”, but not „chodnik”


def song_table(log=print) -> pd.DataFrame:
    from wordfreq import zipf_frequency

    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    own = lines[lines.attributed & ~lines.is_dup]
    words = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["line_uid", "w", "form", "lang"])
    words = words[words.line_uid.isin(own.line_uid)]
    morph = morphology(own, words, log).merge(words, on=["line_uid", "w"])
    morph["low"] = morph.form.str.lower()
    lemmas = set(pd.read_parquet(paths.PARQUET / "words.parquet", columns=["lemma"]).lemma.str.lower())
    vocab = set(morph.low)
    rare = {w for w in vocab if w.isalpha() and len(w) > 3 and zipf_frequency(w, "pl") < RARE_ZIPF}
    dimin = {w for w in vocab if w.isalpha() and is_diminutive(w, lemmas)}
    morph = morph.merge(own[["line_uid", "song_id"]], on="line_uid")
    raw = {s["song_id"]: s["lyrics"] for s in load_songs()}
    rows = []
    for sid, ln in own.groupby("song_id"):
        m = morph[morph.song_id == sid].sort_values(["line_uid", "w"])
        tc, comp = Counter(), 0
        for _, g in m.groupby("line_uid", sort=False):
            tc += tense_counts(g)
            comp += comparisons(g, list(g.form))
        verbs = sum(tc.values()) or 1
        tensed = (tc["past"] + tc["present"] + tc["future"]) or 1
        pl = m[(m.lang == "pl") & m.low.str.isalpha() & ~m.low.map(is_function_word)]
        text = "\n".join(ln.text).encode("utf-8")
        adlibs = [a for a in ADLIB.findall(raw.get(sid, "")) if not REPEAT_MARK.match(a.strip().lower())]
        all_lines = (lines.song_id == sid).sum()
        rows.append({"song_id": sid, "artist": ln.artist.iloc[0], "words": len(m), "lines": len(ln),
                     "past_share": tc["past"] / tensed, "present_share": tc["present"] / tensed,
                     "future_share": tc["future"] / tensed, "imperatives_100_verbs": 100 * tc["imperative"] / verbs,
                     "comparisons_100_lines": 100 * comp / len(ln),
                     "diminutives_1000": 1000 * m.low.isin(dimin).sum() / max(len(m), 1),
                     "rare_words_share": pl.low.isin(rare).mean() if len(pl) else None,
                     "compression": len(zlib.compress(text, 9)) / max(len(text), 1),
                     "adlibs_100_lines": 100 * len(adlibs) / max(all_lines, 1)})
    log(f"songs: {len(rows)}; diminutive forms: {len(dimin)}; rare forms: {len(rare)}")
    return pd.DataFrame(rows)


def artist_table(songs: pd.DataFrame) -> pd.DataFrame:
    w = songs.words
    agg = {"songs": songs.groupby("artist").size()}
    for col in ("past_share", "present_share", "future_share", "imperatives_100_verbs", "diminutives_1000",
                "rare_words_share", "compression"):
        agg[col] = (songs[col] * w).groupby(songs.artist).sum() / w.groupby(songs.artist).sum()
    for col in ("comparisons_100_lines", "adlibs_100_lines"):
        agg[col] = (songs[col] * songs.lines).groupby(songs.artist).sum() / songs.lines.groupby(songs.artist).sum()
    return pd.DataFrame(agg).reset_index()


def adlib_lexicon(top: int = 8) -> pd.DataFrame:
    """Most frequent ad-libs per rapper (whole songs, guests included)."""
    rows = []
    for s in load_songs():
        for a in ADLIB.findall(s["lyrics"]):
            a = a.strip().lower()
            if not REPEAT_MARK.match(a):
                rows.append((s["artist"], a))
    df = pd.DataFrame(rows, columns=["artist", "adlib"])
    out = df.groupby(["artist", "adlib"]).size().rename("count").reset_index()
    return out.sort_values(["artist", "count"], ascending=[True, False]).groupby("artist").head(top)


def collaborations() -> pd.DataFrame:
    """Edges rapper → guest with the number of shared songs (Genius featured artists)."""
    c = Counter((s["artist"], g) for s in load_songs() for g in s["featured"])
    return pd.DataFrame([{"artist": a, "guest": g, "songs": n} for (a, g), n in c.most_common()])


def run(log=print):
    STATS.mkdir(parents=True, exist_ok=True)
    songs = song_table(log)
    songs.to_parquet(STATS / "text_features_songs.parquet", index=False)
    art = artist_table(songs)
    art.to_csv(STATS / "text_features.csv", index=False)
    adlib_lexicon().to_csv(STATS / "adlibs.csv", index=False)
    collaborations().to_csv(STATS / "collaborations.csv", index=False)
    return songs, art


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    print(run()[1].round(3).to_string(index=False))
