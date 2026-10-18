"""Does a DNA feature describe the rapper or the song? (In MCFlow, songs by one rapper often differ more than
rappers do; Condit-Schultz 2016/17, Ohriner 2016.)

Every feature is computed separately for every song (the same functions as the rapper statistics,
`technical.technical_stats`), on lines attributed to the rapper, in songs with at least MIN_LINES such lines. Then:
- **ICC** (intraclass correlation, one-way random model, unequal groups): how much of the variation between songs
  comes from who is rapping. ICC < 0.5 = songs by one rapper differ more than rappers do (the MCFlow situation);
- a 95% interval from leaving out one rapper at a time (jackknife);
- eta² of rapper and decade: how much variation the rapper explains and how much the era alone does;
- **how many songs** are needed for a rapper's mean to reach reliability 0.8 (Spearman–Brown: n = 4 (1 − ICC) / ICC);
- **reliability of the mean** at the actual number of songs (median over rappers).
Features: the validated DNA features (`config/stats.yaml`, dna: true) except those that cannot be computed per song
(vocabulary per 8,000 words → MATTR in a 100-word window), plus function words per 1000 words (stylometry) and
self-mentions per 1000 words; surface features (`stats/surface.py`) and text features (`stats/textual.py`) when
they have been computed.

Usage: python -m rapdna.stats.reliability → data/stats/reliability.csv, data/stats/song_features.parquet
"""
import numpy as np
import pandas as pd

from rapdna import paths
from rapdna.ingest import load_config
from rapdna.stats.surface import self_re
from rapdna.stats.technical import load, mattr, technical_stats

MIN_LINES = 24
FEATURES = ["mattr_100", "rhyme_density", "rhyme_length", "three_plus_share", "rhymed_lines_share", "exact_share",
            "alliterations_100", "anaphoras_100", "epiphoras_100", "phrase_repetitions_100", "syllables_per_line",
            "word_length", "english_share", "self_mentions_1000"]
SURFACE = ["chorus_share", "guests", "rapper_share", "lines_per_verse", "intro_outro", "vulgarisms_1000",
           "slang_1000", "out_of_dictionary_1000"]
TEXT = ["past_share", "present_share", "future_share", "imperatives_100_verbs", "comparisons_100_lines",
        "diminutives_1000", "rare_words_share", "compression", "adlibs_100_lines"]
# the most frequent function words: stylometry (a word fingerprint, plan 3.3)
STYLO = ["się", "nie", "to", "w", "i", "na", "z", "jak", "że", "a", "mi", "do", "co", "ja", "jest", "tak", "mnie",
         "ten", "o", "po", "bo", "za", "tu", "ty", "by", "już", "czy", "tylko", "no", "od"]


def song_features(log=print) -> pd.DataFrame:
    lines, words, rhymes = load()
    selfs = {a["name"]: {a["name"].lower(), *(x.lower() for x in a.get("aliases", []))}
             for a in load_config()["artists"]}
    n_lines = lines.groupby("song_id").size()
    keep = n_lines[n_lines >= MIN_LINES].index
    rows = []
    for k, sid in enumerate(keep):
        ln, wd = lines[lines.song_id == sid], words[words.song_id == sid]
        rh = rhymes[rhymes.line_b.isin(ln.line_uid)]
        st = technical_stats(ln, wd, rh, vocab=False)
        artist = ln.artist.iloc[0]
        forms = wd.form.str.lower()
        row = {"song_id": sid, "artist": artist, "year": ln.year.iloc[0], **st,
               "mattr_100": mattr(list(wd.sort_values(["section", "line", "w"]).lemma.str.lower()), 100)}
        text = " ".join(ln.text).lower()
        row["self_mentions_1000"] = 1000 * len(self_re(list(selfs.get(artist, {artist}))).findall(text)) / len(wd)
        counts = forms.value_counts()
        for w in STYLO:
            row[f"fw_{w}"] = 1000 * counts.get(w, 0) / len(wd)
        rows.append(row)
        if k % 200 == 0:
            log(f"  songs: {k}/{len(keep)}")
    return pd.DataFrame(rows)


def icc(values: np.ndarray, groups: np.ndarray) -> float:
    """ICC(1) for unequal groups (one-way ANOVA)."""
    df = pd.DataFrame({"x": values, "g": groups}).dropna()
    k, N = df.g.nunique(), len(df)
    if k < 2 or N <= k:
        return float("nan")
    gm = df.groupby("g").x
    n_i, mean_i = gm.size(), gm.mean()
    grand = df.x.mean()
    msb = (n_i * (mean_i - grand) ** 2).sum() / (k - 1)
    msw = ((df.x - df.g.map(mean_i)) ** 2).sum() / (N - k)
    n0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    den = msb + (n0 - 1) * msw
    return float((msb - msw) / den) if den > 0 else float("nan")


def eta2(values: np.ndarray, groups: np.ndarray) -> float:
    """Share of variation explained by a grouping (e.g. decade), with no correction for the number of groups."""
    df = pd.DataFrame({"x": values, "g": groups}).dropna()
    m = df.groupby("g").x.transform("mean")
    tot = ((df.x - df.x.mean()) ** 2).sum()
    return float(((m - df.x.mean()) ** 2).sum() / tot) if tot > 0 else float("nan")


def decompose(songs: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """ICC with an interval from leaving out one rapper at a time (jackknife; resampling songs with replacement inflates
    ICC, because a repeated song makes a rapper's songs look alike), rapper vs decade share (eta²)."""
    artists = sorted(songs.artist.unique())
    decade = (songs.year // 10 * 10).to_numpy()
    med_n = int(songs.groupby("artist").size().median())
    rows = []
    for f in features:
        x, g = songs[f].to_numpy(float), songs.artist.to_numpy()
        v = icc(x, g)
        jk = np.array([icc(x[g != a], g[g != a]) for a in artists])
        n = len(artists)
        se = np.sqrt((n - 1) / n * np.nansum((jk - np.nanmean(jk)) ** 2))
        need = 4 * (1 - v) / v if v > 0 else float("inf")
        rows.append({"feature": f, "icc": round(v, 3), "icc_lo": round(v - 1.96 * se, 3), "icc_hi": round(v + 1.96 * se, 3),
                     "eta2_artist": round(eta2(x, g), 3), "eta2_decade": round(eta2(x, decade), 3),
                     "songs_for_reliability_0_8": round(need, 1),
                     f"reliability_at_{med_n}_songs": round(med_n * v / (1 + (med_n - 1) * v), 3) if v > 0 else 0.0})
    return pd.DataFrame(rows).sort_values("icc", ascending=False)


def run(log=print) -> pd.DataFrame:
    out_songs = paths.DATA / "stats" / "song_features.parquet"
    songs = pd.read_parquet(out_songs) if out_songs.exists() else song_features(log)
    songs.to_parquet(out_songs, index=False)
    log(f"songs: {len(songs)}, rappers: {songs.artist.nunique()}")
    feats = FEATURES + [f"fw_{w}" for w in STYLO]
    surface = paths.DATA / "stats" / "surface_features_songs.parquet"
    if surface.exists():
        songs = songs.merge(pd.read_parquet(surface)[["song_id"] + SURFACE], on="song_id", how="left")
        feats += SURFACE
    text = paths.DATA / "stats" / "text_features_songs.parquet"
    if text.exists():
        songs = songs.merge(pd.read_parquet(text)[["song_id"] + TEXT], on="song_id", how="left")
        feats += TEXT
    res = decompose(songs.reset_index(drop=True), feats)
    res.to_csv(paths.DATA / "stats" / "reliability.csv", index=False)
    return res


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    print(run().to_string(index=False))
