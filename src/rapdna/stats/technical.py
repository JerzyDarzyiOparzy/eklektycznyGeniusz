"""Technical statistics per rapper (and per album). Input: data/parquet/{lines,words,rhymes,figures}.parquet.

Only lines attributed to the rapper (their solo sections) are counted, without repeats (a chorus counts once).
Column names match config/stats.yaml, which holds the labels and what each statistic does and does not measure.
"""
import random
from collections import Counter

import numpy as np
import pandas as pd

from rapdna import paths
from rapdna.figures.compute import FIGURE_COLUMNS
from rapdna.rhymes.density import Word, rhyme_density

VOCAB_SAMPLE = 8_000  # words per sample for counting unique lemmas (selection criterion: every rapper has ≥ 8000)
VOCAB_DRAWS = 20
MATTR_WINDOW = 500
SEED = 2026


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    rhymes = pd.read_parquet(paths.PARQUET / "rhymes.parquet")
    lines = lines[lines.attributed & ~lines.is_dup].copy()
    words = words[words.line_uid.isin(lines.line_uid)].merge(
        lines[["line_uid", "artist", "album", "song_id", "section", "line"]], on="line_uid")
    rhymes = rhymes[rhymes.validated & rhymes.line_b.isin(lines.line_uid)]
    rhymes = rhymes.merge(lines[["line_uid", "album"]], left_on="line_b", right_on="line_uid").drop(columns="line_uid")
    figures = pd.read_parquet(paths.PARQUET / "figures.parquet")
    lines = lines.merge(figures, on="line_uid", how="left")
    lines[FIGURE_COLUMNS] = lines[FIGURE_COLUMNS].fillna(False).astype(bool)
    return lines, words, rhymes


def lemma_sequences(words: pd.DataFrame) -> dict[int, list[str]]:
    """Word lemmas in order, separately for every song."""
    w = words.sort_values(["song_id", "section", "line", "w"])
    return {sid: list(g.lemma.str.lower()) for sid, g in w.groupby("song_id", sort=False)}


def vocab_unique(songs: dict[int, list[str]], n: int, draws: int, seed: int = SEED) -> tuple[float, float]:
    """Unique lemmas in the first n words after a random shuffle of songs (mean and standard deviation)."""
    ids = list(songs)
    total = sum(len(v) for v in songs.values())
    if total < n:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    counts = []
    for _ in range(draws):
        rng.shuffle(ids)
        seq = [lem for sid in ids for lem in songs[sid]][:n]
        counts.append(len(set(seq)))
    return float(np.mean(counts)), float(np.std(counts))


def mattr(seq: list[str], window: int = MATTR_WINDOW) -> float:
    """Moving-average type-token ratio: mean share of unique lemmas in a sliding window."""
    if len(seq) < window:
        return float("nan")
    c = Counter(seq[:window])
    ratios = [len(c) / window]
    for i in range(window, len(seq)):
        c[seq[i]] += 1
        old = seq[i - window]
        c[old] -= 1
        if not c[old]:
            del c[old]
        ratios.append(len(c) / window)
    return float(np.mean(ratios))


def section_lines(words: pd.DataFrame):
    """Iterates over sections: a list of lines, each line a DataFrame of words."""
    w = words.sort_values(["song_id", "section", "line", "w"])
    for _, sec in w.groupby(["song_id", "section"], sort=False):
        yield [g for _, g in sec.groupby("line", sort=True)]


def technical_stats(lines: pd.DataFrame, words: pd.DataFrame, rhymes: pd.DataFrame, vocab: bool = True) -> dict:
    n_lines = len(lines)
    out: dict[str, float] = {"lines": n_lines, "words": len(words)}

    songs = lemma_sequences(words)
    if vocab:
        out["vocabulary"], out["vocabulary_sd"] = vocab_unique(songs, VOCAB_SAMPLE, VOCAB_DRAWS)
    out["mattr"] = mattr([lem for seq in songs.values() for lem in seq])

    dens_sum = dens_n = 0
    for sec in section_lines(words):
        word_lines = [[Word(r.form, r.ipa, r.function) for r in ln.itertuples()] for ln in sec]
        d, n = rhyme_density(word_lines)
        dens_sum += d * n
        dens_n += n
    out["rhyme_density"] = dens_sum / dens_n if dens_n else float("nan")

    end = rhymes[(rhymes.kind == "end") & rhymes.best]  # the best partner of every line
    out["rhyme_length"] = end.syllables.mean()
    out["multisyllabic_share"] = (end.syllables >= 2).mean()
    out["three_plus_share"] = (end.syllables >= 3).mean()
    # a rhymed line rhymes its ending with an earlier or a later line (within 3 lines)
    out["rhymed_lines_share"] = len(set(end.line_a) | set(end.line_b)) / n_lines
    internal = rhymes[rhymes.kind == "internal"]
    out["internal_rhymes_100"] = 100 * (internal.anchor == "clausal").sum() / n_lines
    out["inword_rhymes_100"] = 100 * (internal.anchor == "in_word").sum() / n_lines
    for t in ("exact", "assonance", "approx", "consonance"):
        out[f"{t}_share"] = (end.type == t).mean()
    # axes from the glossary (docs/en/glossary.md) for end rhymes
    out["rich_share"] = end.rich.mean()
    out["grammatical_share"] = end.grammatical.mean()
    out["shifted_stress_share"] = (~end.stress_ok.astype(bool)).mean()
    # figures from data/parquet/figures.parquet: per 100 lines (enjambment as a share of lines)
    for col in FIGURE_COLUMNS:
        out[f"{col}s_100"] = 100 * lines[col].sum() / n_lines

    syll = words.groupby("line_uid").n_syll.sum()
    out["syllables_per_line"] = syll.mean()
    out["syllables_per_line_sd"] = syll.std()
    content = words[~words.function]
    out["word_length"] = content.n_syll.mean()
    out["english_share"] = (words.lang == "en").mean()
    return out


def compute(log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    from rapdna.rhymes.ruler_corpus import internal_excess
    from rapdna.stats.schemes import compute as schemes

    lines, words, rhymes = load()
    log("  internal rhymes above chance…")
    excess = internal_excess(pd.read_parquet(paths.PARQUET / "lines.parquet"),
                             pd.read_parquet(paths.PARQUET / "words.parquet"))
    log("  rhyme schemes…")
    sch = schemes(log=log)[0].set_index("artist").drop(columns="quatrains").to_dict("index")
    per_artist, per_album = [], []
    for artist, la in lines.groupby("artist"):
        log(f"  {artist}")
        wa, ra = words[words.artist == artist], rhymes[rhymes.artist == artist]
        per_artist.append({"artist": artist, **technical_stats(la, wa, ra), **excess.get(artist, {}), **sch.get(artist, {})})
        for album, lb in la.groupby("album"):
            year = lb.year.min()
            per_album.append({"artist": artist, "album": album, "year": year,
                              **technical_stats(lb, wa[wa.album == album], ra[ra.album == album], vocab=False)})
    return pd.DataFrame(per_artist), pd.DataFrame(per_album)
