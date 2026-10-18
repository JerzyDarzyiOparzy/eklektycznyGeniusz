"""Meaning-based figures (plan, phase 3): candidates for puns, double meanings and paronomasia, and their review.

Candidates come from two sources:
- fan annotations on Genius that talk about wordplay („gra słów”, „podwójne znaczenie”, „brzmi jak”…); fans explain
  exactly these; only fragments from the rapper's own lines are kept;
- paronomasia from Parrish sound vectors (figures/candidates.py).
Confirmation: a manual review of every candidate (data/candidates/wordplay_review.csv). Only confirmed ones reach the
page, as examples; the count is not compared, because it depends on how active a rapper's fans are.
"""
import re

import pandas as pd

from rapdna import paths
from rapdna.text.sections import norm_line

OUT = paths.DATA / "candidates"
WORDPLAY = (r"gra słów|grą słów|gry słów|grę słów|dwuznaczn|podwójn\w* znaczeni|podwójn\w* sens|kalambur|przekmin|"
            r"homonim|homofon|brzmi jak|brzmieni|zabaw\w* słow|wordplay|double entendre|punchline|dwa znaczenia|"
            r"drugie dno|znaczy też|może oznaczać|odnosi się zarówno|w dwojakim")


def annotation_candidates() -> pd.DataFrame:
    a = pd.read_json(paths.DATA / "annotations.jsonl", lines=True)
    a = a[a.body.str.contains(WORDPLAY, case=False, regex=True)]
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    own = lines[lines.attributed & ~lines.is_dup]
    keys = {(r.song_id, norm_line(r.text)) for r in own.itertuples()}
    rows = []
    for r in a.itertuples():
        frag_lines = [norm_line(x) for x in re.split(r"\n", r.fragment) if norm_line(x)]
        if frag_lines and any((r.song_id, fl) in keys for fl in frag_lines):
            rows.append({"artist": r.artist, "title": r.title, "fragment": r.fragment.replace("\n", " / "),
                         "votes": r.votes, "annotation": re.sub(r"\s+", " ", r.body)[:600]})
    return pd.DataFrame(rows).drop_duplicates(["artist", "fragment"]).reset_index(drop=True)


def confirmed() -> pd.DataFrame:
    """Confirmed wordplay: from annotations (wordplay_review.csv) and paronomasia (paronomasia_review.csv), no duplicates.
    The `source` values are shown on the page, so they stay Polish."""
    a = pd.read_csv(OUT / "wordplay_review.csv", sep=";", encoding="utf-8-sig")
    a = a[a.confirmed == 1].assign(source="adnotacja fanów")[["artist", "title", "fragment", "votes", "source"]]
    p = pd.read_csv(OUT / "paronomasia_review.csv", sep=";", encoding="utf-8-sig")
    p = p[p.confirmed == 1].assign(source="paronomazja (wektory brzmienia)", votes=0)
    p = p.rename(columns={"text": "fragment"})[["artist", "title", "fragment", "votes", "source"]]
    seen = {norm_line(f.split(" / ")[0]) for f in a.fragment}
    p = p[~p.fragment.map(lambda f: any(norm_line(f) in s or s in norm_line(f) for s in seen))]
    out = pd.concat([a, p], ignore_index=True)
    out.to_csv(OUT / "wordplay_confirmed.csv", sep=";", index=False, encoding="utf-8-sig")
    return out
