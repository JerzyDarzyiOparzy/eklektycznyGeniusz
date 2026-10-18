"""Variant R over the whole corpus: rhyme candidates in every verse → data/parquet/rhymes_r.parquet.

Line pairs within a verse: the same line, the neighbouring line (all anchors) and up to 3 lines away (end rhymes of
both lines only). Repeated lines (same text) are skipped, and the same pair of texts counts once per song.
"""
import random

import pandas as pd

from rapdna import paths
from rapdna.rhymes.match import FAR_WINDOW, build_line, describe, find, select, thresholds

OUT = paths.PARQUET / "rhymes_r.parquet"
SAMPLE_FLOOR = {"clausal": -5.0, "in_word": -5.0, "consonance": -5.0}  # for drawing gold sets: also below thresholds
CHANCE_PAIRS = 3000
CHANCE_SEED = 2026


def lines_by_uid(lines_df: pd.DataFrame, words_df: pd.DataFrame) -> dict:
    w = words_df[words_df.line_uid.isin(lines_df.line_uid)].sort_values(["line_uid", "w"])
    return {u: build_line(list(zip(g.form, g.ipa, g.lemma, g.pos))) for u, g in w.groupby("line_uid", sort=False)}


def eligible_lines(lines_df: pd.DataFrame) -> pd.DataFrame:
    """The rapper's own lines in sections that can carry rhymes, without repeats."""
    from rapdna.pipeline import RHYME_SECTIONS

    return lines_df[~lines_df.is_dup & lines_df.attributed & lines_df.section_type.isin(RHYME_SECTIONS)]


def detect(lines_df: pd.DataFrame, words_df: pd.DataFrame, th: dict | None = None, log=print) -> pd.DataFrame:
    """All candidates above `th` (default: config/thresholds_r.yaml), described on the dictionary axes."""
    th = th or thresholds()
    eligible = eligible_lines(lines_df)
    built = lines_by_uid(eligible, words_df)
    text = eligible.set_index("line_uid").text.str.lower()
    rows, seen = [], set()
    groups = eligible.sort_values(["song_id", "section", "line"]).groupby(["song_id", "section"], sort=False)
    for n, ((song_id, _), g) in enumerate(groups):
        uids = [u for u in g.line_uid if u in built]
        artist = g.artist.iloc[0]
        for x, ua in enumerate(uids):
            for d in range(0, FAR_WINDOW + 1):
                if x + d >= len(uids):
                    break
                ub = uids[x + d]
                if d and text[ua] == text[ub]:
                    continue
                key = tuple(sorted((text[ua], text[ub]))) + (d == 0,)
                if key in seen:
                    continue
                seen.add(key)
                a, b = built[ua], built[ub]
                for m in select(a, b, find(a, b, same=(d == 0), far=(d >= 2)), th):
                    rows.append({"song_id": song_id, "artist": artist, "line_a": ua, "line_b": ub, "distance": d,
                                 **describe(a, b, m)})
        if n % 2000 == 0:
            log(f"  verses: {n}, candidates: {len(rows)}")
    return pd.DataFrame(rows)


def run(log=print) -> dict:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    df = detect(lines, words, log=log)
    df.to_parquet(OUT, index=False)
    return {"rhymes_r": len(df), **df.anchor.value_counts().to_dict()}


def internal_excess(lines_df: pd.DataFrame, words_df: pd.DataFrame, th: dict | None = None) -> dict[str, dict]:
    """Internal rhymes above chance, per rapper: the share of neighbouring line pairs with an internal rhyme (at least
    one side not at the line end) minus the same share in random pairs of his lines from different songs.
    Random pairs share the rapper's vocabulary and style, so the difference shows intended, not accidental, rhyme."""
    th = th or thresholds()
    eligible = eligible_lines(lines_df).sort_values(["song_id", "section", "line"])
    built = lines_by_uid(eligible, words_df)
    song = eligible.set_index("line_uid").song_id
    rng = random.Random(CHANCE_SEED)

    def rate(pairs):
        hits = 0
        for ua, ub in pairs:
            a, b = built[ua], built[ub]
            ms = select(a, b, find(a, b), th)
            hits += any(m.anchor != "consonance" and not (m.i1 == len(a.ks) - 1 and m.j1 == len(b.ks) - 1) for m in ms)
        return hits / len(pairs) if pairs else float("nan")

    out = {}
    for artist, g in eligible.groupby("artist"):
        adj = [(x, y) for _, s in g.groupby(["song_id", "section"], sort=False)
               for x, y in zip(s.line_uid, s.line_uid.iloc[1:]) if x in built and y in built]
        uids = [u for u in g.line_uid if u in built]
        rand = []
        while len(rand) < min(CHANCE_PAIRS, len(adj)) and len(uids) > 1:
            x, y = rng.choice(uids), rng.choice(uids)
            if song[x] != song[y]:
                rand.append((x, y))
        adj = rng.sample(adj, min(CHANCE_PAIRS, len(adj)))
        r_adj, r_rand = rate(adj), rate(rand)
        se = (r_adj * (1 - r_adj) / max(len(adj), 1) + r_rand * (1 - r_rand) / max(len(rand), 1)) ** 0.5
        out[artist] = {"internal_rhymes_excess": 100 * (r_adj - r_rand), "internal_rhymes_excess_se": 100 * se,
                       "internal_rhymes_adjacent": r_adj, "internal_rhymes_random": r_rand}
    return out
