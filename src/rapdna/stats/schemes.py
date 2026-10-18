"""Rhyme schemes in a verse (docs/en/glossary.md): AABB, ABAB, ABBA, monorhyme.

A verse is cut into consecutive quatrains from its start (the rapper's lines, without repeats). The scheme of a quatrain
follows from the end-rhyme pairs (all pairs up to 3 lines apart, not only the best partner):
- monorhyme (AAAA): 1–2, 2–3 and 3–4 rhyme;
- AABB: 1–2 and 3–4, but not 2–3;
- ABAB: 1–3 and 2–4, but not 1–2 or 3–4;
- ABBA: 1–4 and 2–3, but not 1–2 or 3–4;
- other: any other layout, also no rhymes at all.
Chance control: the same rules on quatrains of random lines of the rapper taken from different songs.
"""
import random

import pandas as pd

from rapdna import paths

SCHEMES = ["monorhyme", "aabb", "abab", "abba", "other"]
SEED = 2026


def classify(r) -> str:
    """r(i, j): whether lines i, j (0–3) rhyme at their ends."""
    if r(0, 1) and r(1, 2) and r(2, 3):
        return "monorhyme"
    if r(0, 1) and r(2, 3) and not r(1, 2):
        return "aabb"
    if r(0, 2) and r(1, 3) and not r(0, 1) and not r(2, 3):
        return "abab"
    if r(0, 3) and r(1, 2) and not r(0, 1) and not r(2, 3):
        return "abba"
    return "other"


def quatrains(lines: pd.DataFrame) -> list[tuple[str, list[str]]]:
    """(rapper, 4 consecutive uids) for the rapper's lines in verses, from the start of the verse."""
    from rapdna.pipeline import RHYME_SECTIONS

    e = lines[~lines.is_dup & lines.attributed & lines.section_type.isin(RHYME_SECTIONS)]
    out = []
    for _, g in e.sort_values(["song_id", "section", "line"]).groupby(["song_id", "section"], sort=False):
        uids = list(g.line_uid)
        out += [(g.artist.iloc[0], uids[i:i + 4]) for i in range(0, len(uids) - 3, 4)]
    return out


def compute(log=print) -> tuple[pd.DataFrame, pd.Series]:
    """Share of each scheme per rapper (from the data) and in random quatrains (chance control)."""
    from rapdna.rhymes.match import find, select, thresholds
    from rapdna.rhymes.ruler_corpus import lines_by_uid

    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    rh = pd.read_parquet(paths.PARQUET / "rhymes.parquet")
    end = rh[(rh.kind == "end") & rh.validated]
    pairs = set(zip(end.line_a, end.line_b)) | set(zip(end.line_b, end.line_a))
    qs = quatrains(lines)
    real = pd.DataFrame([{"artist": a, "scheme": classify(lambda i, j: (q[i], q[j]) in pairs)} for a, q in qs])

    # chance control: 4 random lines of the rapper from 4 different songs, rhymes found by the same rules
    rng, th = random.Random(SEED), thresholds()
    song = lines.set_index("line_uid").song_id
    pool = {a: [u for _, q in grp for u in q] for a, grp in pd.Series(qs).groupby([a for a, _ in qs])}
    fake = []
    for a, uids in pool.items():
        for _ in range(min(500, len(uids) // 4)):
            q = rng.sample(uids, 4)
            if len({song[u] for u in q}) == 4:
                fake.append((a, q))
    built = lines_by_uid(lines[lines.line_uid.isin({u for _, q in fake for u in q})],
                         pd.read_parquet(paths.PARQUET / "words.parquet"))

    def rhyme(x, y):
        a, b = built.get(x), built.get(y)
        if not a or not b:
            return False
        return any(m.anchor == "clausal" and m.i1 == len(a.ks) - 1 and m.j1 == len(b.ks) - 1
                   for m in select(a, b, find(a, b, far=True), th))

    rand = pd.DataFrame([{"artist": a, "scheme": classify(lambda i, j: rhyme(q[i], q[j]))} for a, q in fake])
    out = pd.crosstab(real.artist, real.scheme, normalize="index").reindex(columns=SCHEMES, fill_value=0)
    out.columns = [f"scheme_{c}" for c in out.columns]
    out["quatrains"] = real.groupby("artist").size()
    chance = rand.scheme.value_counts(normalize=True).reindex(SCHEMES, fill_value=0)
    log("  chance (random quatrains): " + ", ".join(f"{k} {v:.3f}" for k, v in chance.items()))
    return out.reset_index(), chance
