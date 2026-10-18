"""Stylistic figures for every rapper line (without repeats) → data/parquet/figures.parquet.

0/1 columns: alliteration, assonance_chain, consonance_chain, onomatopoeia, anaphora, epiphora, phrase_repetition,
parallelism (with the previous line), enjambment (the line runs on into the next one).
"""
import pandas as pd

from rapdna import paths
from rapdna.figures import enjambment
from rapdna.figures.repetition import has_phrase_repetition, is_anaphora, is_epiphora, is_parallelism
from rapdna.figures.sound import (
    find_alliterations,
    find_assonance_chains,
    find_consonance_chains,
    find_onomatopoeia,
)

FIGURE_COLUMNS = ["alliteration", "assonance_chain", "consonance_chain", "onomatopoeia", "anaphora", "epiphora",
                  "phrase_repetition", "parallelism", "enjambment"]


def compute(log=print) -> pd.DataFrame:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    lines = lines[lines.attributed & ~lines.is_dup].sort_values(["song_id", "section", "line"])
    words = words[words.line_uid.isin(lines.line_uid)]
    vocab = sorted(set(words.form.str.lower()))
    in_dict = set(pd.read_parquet(paths.PHONETIC_DICT, columns=["word"], filters=[("word", "in", vocab)]).word)
    by_line = {u: g.sort_values("w") for u, g in words.groupby("line_uid")}

    rows = []
    for _, sec in lines.groupby(["song_id", "section"], sort=False):
        uids = list(sec.line_uid)
        for k, uid in enumerate(uids):
            w = by_line.get(uid)
            if w is None:
                continue
            quad = list(zip(w.form, w.lemma, w.ipa, w.function))
            forms = list(w.form.str.lower())
            pw = by_line.get(uids[k - 1]) if k else None
            prev = list(pw.form.str.lower()) if pw is not None else []
            prev_pos = list(pw.pos) if pw is not None else []
            row = {
                "line_uid": uid,
                "alliteration": bool(find_alliterations(quad)),
                "assonance_chain": bool(find_assonance_chains(quad)),
                "consonance_chain": bool(find_consonance_chains(quad)),
                "onomatopoeia": bool(find_onomatopoeia(quad, in_dict)),
                "anaphora": is_anaphora(prev, forms),
                "epiphora": is_epiphora(prev, forms),
                "phrase_repetition": has_phrase_repetition(prev, forms, list(~w.function.astype(bool))),
                "parallelism": is_parallelism(prev_pos, list(w.pos), prev, forms),
            }
            has_next = k + 1 < len(uids) and uids[k + 1] in by_line
            row["enjambment"] = has_next and enjambment.hanging_end(w.form.iloc[-1], w.pos.iloc[-1])
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_parquet(paths.PARQUET / "figures.parquet", index=False)
    return df
