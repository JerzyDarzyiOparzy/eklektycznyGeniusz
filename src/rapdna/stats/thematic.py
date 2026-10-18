"""Thematic layer (plan, phase 5): the part without embeddings.

- perspective: share of 1st person singular („ja”), 1st person plural („my”), 2nd person („ty/wy”) and 3rd person
  plural („oni”) forms among personal pronouns and verbs with a marked person (spaCy: Person, Number);
- references: proper names from spaCy NER (people, places, organisations and brands) and rapper names from Genius,
  per 1000 words, with a list of the most frequent ones;
- Genius annotations: fragments with fan explanations (with vote counts) as hints for references and wordplay,
  marked as interpretation, not fact.
The reference kinds („osoba”, „miejsce”…) are shown on the page, so they stay Polish.
"""
import json
from collections import Counter

import pandas as pd

from rapdna import paths

NER_CACHE = paths.DATA / "ner_cache.json"
ANNOTATIONS = paths.DATA / "annotations.jsonl"
NER_LABELS = {"persName": "osoba", "placeName": "miejsce", "geogName": "miejsce", "orgName": "organizacja/marka"}


def perspective(words: pd.DataFrame) -> dict[str, float]:
    w = words[(words.person != "") & words.pos.isin(["PRON", "VERB", "AUX"])]
    n = len(w)
    if not n:
        return {}
    i = ((w.person == "1") & (w.number == "Sing")).sum()
    we = ((w.person == "1") & (w.number == "Plur")).sum()
    you = (w.person == "2").sum()
    they = ((w.person == "3") & (w.number == "Plur")).sum()
    return {"perspective_i": i / n, "perspective_we": we / n, "perspective_you": you / n, "perspective_they": they / n}


def ner(texts: list[str], log=print) -> dict[str, list[tuple[str, str]]]:
    cache = json.loads(NER_CACHE.read_text(encoding="utf-8")) if NER_CACHE.exists() else {}
    todo = sorted({t for t in texts if t not in cache})
    if todo:
        import spacy

        log(f"spaCy NER: {len(todo)} lines…")
        nlp = spacy.load("pl_core_news_lg", exclude=["parser", "lemmatizer"])
        for t, doc in zip(todo, nlp.pipe(todo, batch_size=512)):
            cache[t] = [(e.text, e.label_) for e in doc.ents if e.label_ in NER_LABELS]
        NER_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {t: cache.get(t, []) for t in texts}


def rapper_names() -> set[str]:
    """Names of all performers in the corpus (rappers and guests), for detecting references to other rappers."""
    from rapdna.ingest import load_songs

    names = set()
    for s in load_songs():
        names.add(s["artist"])
        names.update(s["featured"])
    return {n for n in names if len(n) >= 3}


NOT_NAMES = {"lala", "lola", "boże", "chryste", "jezu", "polack", "ej", "yeah"}


def _plausible(ent: str, text: str, common: set[str], self_names: set[str]) -> bool:
    """Filter for NER errors (validation: 32/100 false before the filter): ordinary words capitalised at the line start,
    lower case, chorus words and interjections, a rapper naming themself."""
    low = ent.lower()
    if low in NOT_NAMES or low in self_names or any(low in n or n in low for n in self_names if len(n) >= 4):
        return False
    tokens = ent.split()
    if len(tokens) > 1:
        return True
    if not ent[:1].isupper():
        return False
    at_start = text.lstrip(" \"'„-\u2014\u2013([").startswith(ent)
    return not (at_start and low in common)


def references(lines: pd.DataFrame, n_words: dict[str, int], log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(references per 1000 words by rapper and kind, list of occurrences)."""
    from rapdna.ingest import load_config

    ents = ner(list(lines.text), log=log)
    raps = rapper_names()
    cands = sorted({e.lower() for v in ents.values() for e, _ in v if " " not in e})
    common = set(pd.read_parquet(paths.PHONETIC_DICT, columns=["word"], filters=[("word", "in", cands)]).word)
    selfs = {a["name"]: {a["name"].lower(), *(x.lower() for x in a.get("aliases", []))}
             for a in load_config()["artists"]}
    rows = []
    for r in lines.itertuples():
        me = selfs.get(r.artist, {r.artist.lower()})
        found = {(e, NER_LABELS[l]) for e, l in ents[r.text] if _plausible(e, r.text, common, me)}
        low = r.text.lower()
        for name in raps:
            if name.lower() not in me and f" {name.lower()} " in f" {low} ":
                found.add((name, "raper"))
        for ent, kind in found:
            rows.append({"artist": r.artist, "line_uid": r.line_uid, "reference": ent, "kind": kind})
    occ = pd.DataFrame(rows)
    stats = occ.groupby(["artist", "kind"]).size().unstack(fill_value=0)
    stats = stats.div(pd.Series(n_words), axis=0) * 1000
    stats["references_1000"] = stats.sum(axis=1)
    return stats.reset_index(), occ


def fetch_annotations(log=print) -> int:
    from rapdna.genius.api import GeniusAPI
    from rapdna.ingest import load_songs

    api = GeniusAPI()
    done = set()
    if ANNOTATIONS.exists():
        done = {json.loads(l)["song_id"] for l in ANNOTATIONS.open(encoding="utf-8")}
    n = 0
    with ANNOTATIONS.open("a", encoding="utf-8") as out:
        for s in load_songs():
            if s["song_id"] in done:
                continue
            for ref in api.referents(s["song_id"]):
                for ann in ref.get("annotations", []):
                    out.write(json.dumps({
                        "song_id": s["song_id"], "artist": s["artist"], "title": s["title"],
                        "fragment": ref.get("fragment", ""), "votes": ann.get("votes_total", 0),
                        "verified": ann.get("verified", False),
                        "body": (ann.get("body") or {}).get("plain", "")[:1500],
                    }, ensure_ascii=False) + "\n")
                    n += 1
            done.add(s["song_id"])
    return n


def compute(log=print) -> pd.DataFrame:
    """Thematic statistics per rapper → data/stats/thematic.csv (+ references in separate files)."""
    from rapdna.stats.domains import domain_shares
    from rapdna.stats.technical import load
    from rapdna.stats.topics import OUT as TOPICS

    lines, words, _ = load()
    lex = json.loads((TOPICS / "domain_lexicons.json").read_text(encoding="utf-8"))
    n_words = words.groupby("artist").size().to_dict()
    ref_stats, occ = references(lines, n_words, log=log)
    rows = []
    for artist, w in words.groupby("artist"):
        rows.append({"artist": artist, **perspective(w), **domain_shares(w, lex)})
    df = pd.DataFrame(rows).merge(ref_stats, on="artist", how="left")
    out = paths.DATA / "stats"
    df.to_csv(out / "thematic.csv", index=False)
    top = (occ.groupby(["artist", "reference", "kind"]).size().rename("n").reset_index()
           .sort_values(["artist", "n"], ascending=[True, False]).groupby("artist").head(15))
    top.to_csv(out / "references_top.csv", index=False)
    occ.to_csv(out / "references_occurrences.csv", index=False)
    return df
