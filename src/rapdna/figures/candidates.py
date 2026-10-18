"""Candidates for meaning-based figures (plan: the machine only points, a person confirms; only confirmed ones reach
the page).

- homophones: a word sounds exactly like a word with another lemma („może” / „morze”): candidate for a sound pun;
- polysemy: the lemma has senses from at least two different domains in Słowosieć (homonyms_cleaned.json) and stands
  at the line end (punchline position): candidate for a double meaning;
- paronomasia: two nearby content words (≤ 3 apart) that sound similar by Parrish vectors, with different lemmas and
  no rhyme at the end, e.g. „czysto / trzysta”.
Files: data/candidates/*.csv with an empty `confirmed` column to fill in.
"""
import json
import unicodedata

import numpy as np
import pandas as pd

from rapdna import paths
from rapdna.phonology import soundvec
from rapdna.rhymes.hb_detect import same_stem

OUT = paths.DATA / "candidates"
PARONOMASIA_MIN = 0.85


def _plain(s: str) -> str:
    """Without Polish diacritics: „czuje” and „czuję” is a typo, not a pun."""
    s = s.lower().replace("ł", "l")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def build(log=print) -> dict[str, int]:
    from wordfreq import zipf_frequency

    OUT.mkdir(parents=True, exist_ok=True)
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    lines = lines[lines.attributed & ~lines.is_dup]
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    words = words[words.line_uid.isin(lines.line_uid)].merge(lines[["line_uid", "artist", "title", "text"]], on="line_uid")
    content = words[~words.function & (words.form.str.len() >= 3)].copy()
    content["f"] = content.form.str.lower()

    # homophones
    d = pd.read_parquet(paths.PHONETIC_DICT, filters=[("ipa", "in", sorted(set(content.ipa)))])
    lemmas_by_ipa = d.groupby("ipa").agg(lemmas=("lemma", lambda s: sorted(set(s.str.lower()))),
                                         words=("word", lambda s: sorted(set(s))))
    h = content.merge(lemmas_by_ipa, left_on="ipa", right_index=True)
    # the partner must be a word in real use (odd dictionary forms drop out: „teras”, „paczę”)
    h = h.assign(other=h.apply(lambda r: [w for w in r.words if _plain(w) != _plain(r.f)
                                          and zipf_frequency(w, "pl") >= 2.5], axis=1))
    h = h[h.other.str.len() > 0]
    h = h.assign(other_words=h.other.map(lambda w: ", ".join(w)[:80]))
    homo = h[["artist", "title", "text", "form", "other_words"]].drop_duplicates(["artist", "text", "form"])

    # polysemy in the punchline position
    hom = json.loads(paths.HOMONYMS.read_text(encoding="utf-8"))
    multi = {k.lower(): sorted({s.get("domain", "") for s in v}) for k, v in hom.items()
             if len({s.get("domain", "") for s in v}) >= 2}
    last = content.sort_values("w").groupby("line_uid").tail(1)
    poly = last[last.lemma.isin(multi) & (last.pos == "NOUN")]
    poly = poly.assign(domains=poly.lemma.map(lambda lem: ", ".join(multi[lem][:4])))
    poly = poly[["artist", "title", "text", "form", "lemma", "domains"]].drop_duplicates(["artist", "text", "form"])

    # paronomasia (Parrish sound vectors)
    vec = soundvec.load()
    par = []
    for _, g in content.sort_values("w").groupby("line_uid"):
        rows = list(g.itertuples())
        for i, a in enumerate(rows):
            for b in rows[i + 1:i + 4]:
                if a.f not in vec or b.f not in vec or a.lemma == b.lemma or same_stem(a.f, b.f):
                    continue
                if a.ipa[-3:] == b.ipa[-3:]:
                    continue  # rather a rhyme than paronomasia
                s = float(np.dot(vec[a.f], vec[b.f]))
                if s >= PARONOMASIA_MIN:
                    par.append({"artist": a.artist, "title": a.title, "text": a.text, "word_a": a.form,
                                "word_b": b.form, "similarity": round(s, 3)})
    paro = (pd.DataFrame(par).drop_duplicates(["artist", "text", "word_a", "word_b"])
            .sort_values("similarity", ascending=False)) if par else pd.DataFrame()

    out = {}
    for name, df in (("homophones", homo), ("polysemy", poly), ("paronomasia", paro)):
        df = df.assign(confirmed="", notes="")
        df.to_csv(OUT / f"{name}.csv", sep=";", index=False, encoding="utf-8-sig")
        out[name] = len(df)
    return out
