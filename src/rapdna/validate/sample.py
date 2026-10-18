"""Random samples of detected rhymes and figures for a manual review in a spreadsheet (columns `ok` and `uwagi` to fill
in; the sheets are Polish, for a Polish reviewer)."""
import pandas as pd

from rapdna import paths

SAMPLES = paths.DATA / "validation"


def _mark(words: pd.DataFrame, uid: str, w: int) -> str:
    toks = words[words.line_uid == uid].sort_values("w")
    return " ".join(f"«{f}»" if i == w else f for i, f in zip(toks.w, toks.form))


def rhyme_sample(n: int = 50, seed: int = 42) -> pd.DataFrame:
    rhymes = pd.read_parquet(paths.PARQUET / "rhymes.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    # strata by kind and type, proportional, but at least 3 examples each
    parts = [
        g.sample(min(len(g), max(3, round(n * len(g) / len(rhymes)))), random_state=seed)
        for _, g in rhymes.groupby(["kind", "type"])
    ]
    sample = pd.concat(parts).sample(frac=1, random_state=seed).head(n).reset_index(drop=True)
    sample["wers_a"] = [_mark(words, r.line_a, r.word_a) for r in sample.itertuples()]
    sample["wers_b"] = [_mark(words, r.line_b, r.word_b) for r in sample.itertuples()]
    ipa = words.set_index(["line_uid", "w"]).ipa
    sample["ipa_a"] = [ipa.get((r.line_a, r.word_a), "") for r in sample.itertuples()]
    sample["ipa_b"] = [ipa.get((r.line_b, r.word_b), "") for r in sample.itertuples()]
    sample["ok"] = ""
    sample["uwagi"] = ""
    return sample[["artist", "kind", "type", "syllables", "score", "wers_a", "wers_b", "ipa_a", "ipa_b", "ok", "uwagi"]]


def figure_sample(n: int = 30, seed: int = 42) -> pd.DataFrame:
    """Random occurrences of alliteration, anaphora and epiphora (n of each) for a manual review."""
    from rapdna.figures.repetition import is_anaphora, is_epiphora
    from rapdna.figures.sound import find_alliterations
    from rapdna.stats.technical import load, section_lines

    _, words, _ = load()
    found = {"aliteracja": [], "anafora": [], "epifora": []}
    for sec in section_lines(words):
        forms = [list(ln.form.str.lower()) for ln in sec]
        for k, ln in enumerate(sec):
            for a in find_alliterations(list(zip(ln.form, ln.lemma, ln.ipa, ln.function))):
                marked = " ".join(f"«{f}»" if i in a.words else f for i, f in enumerate(ln.form))
                found["aliteracja"].append((ln.artist.iloc[0], marked, ""))
            if k:
                prev = " ".join(sec[k - 1].form)
                cur = " ".join(ln.form)
                if is_anaphora(forms[k - 1], forms[k]):
                    found["anafora"].append((ln.artist.iloc[0], prev, cur))
                if is_epiphora(forms[k - 1], forms[k]):
                    found["epifora"].append((ln.artist.iloc[0], prev, cur))
    rows = []
    for kind, items in found.items():
        rng = pd.Series(range(len(items))).sample(min(n, len(items)), random_state=seed)
        rows += [{"figura": kind, "artist": items[i][0], "wers_a": items[i][1], "wers_b": items[i][2]} for i in rng]
    out = pd.DataFrame(rows)
    out["ok"] = ""
    out["uwagi"] = ""
    return out
