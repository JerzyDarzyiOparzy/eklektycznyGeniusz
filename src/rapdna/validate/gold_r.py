"""Gold set of the rule-based ruler (variant R, docs/en/methodology.md): 300 candidates, 100 per anchor,
evenly from every score decile (below the thresholds too). The annotator fills in `rym` (0/1) and `typ` (rhyme kind
code). The sheet is Polish, for a Polish annotator.
"""
import pandas as pd

from rapdna import paths

GOLD_R = paths.DATA / "validation" / "gold_r"
PER_ANCHOR = 100
SEED = 2026
TYPE_CODE = {"d": "exact", "a": "assonance", "k": "consonance", "p": "approx"}  # dokładny, asonans, konsonans, przybliżony


def _fragment(text_words: list[tuple[str, str]], ks, k_range) -> tuple[str, str]:
    """The line with [brackets] around the words covered by the rhyme, and the pronunciation of those words."""
    words = sorted({ks[u].word for u in range(k_range[0], k_range[1] + 1)})
    shown = " ".join(f"[{f}]" if i in words else f for i, (f, _) in enumerate(text_words))
    return shown, " ".join(text_words[i][1] for i in words)


def _lines(uids: set[str]) -> dict:
    from rapdna.rhymes.match import build_line

    w = pd.read_parquet(paths.PARQUET / "words.parquet")
    w = w[w.line_uid.isin(uids)].sort_values(["line_uid", "w"])
    return {u: build_line(list(zip(g.form, g.ipa, g.lemma, g.pos))) for u, g in w.groupby("line_uid")}


def build() -> int:
    from rapdna.rhymes.match import build_line
    from rapdna.rhymes.ruler_corpus import SAMPLE_FLOOR, detect

    cands = detect(pd.read_parquet(paths.PARQUET / "lines.parquet"), pd.read_parquet(paths.PARQUET / "words.parquet"),
                   th=SAMPLE_FLOOR)
    parts = []
    for _, g in cands.groupby("anchor"):
        g = g.assign(decile=pd.qcut(g.score.rank(method="first"), 10, labels=False))
        parts.append(g.groupby("decile", group_keys=False).apply(
            lambda x: x.sample(PER_ANCHOR // 10, random_state=SEED)))
    sample = pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)
    w = pd.read_parquet(paths.PARQUET / "words.parquet")
    w = w[w.line_uid.isin(set(sample.line_a) | set(sample.line_b))].sort_values(["line_uid", "w"])
    by = {u: list(zip(g.form, g.ipa, g.lemma, g.pos)) for u, g in w.groupby("line_uid")}
    rows = []
    for i, r in sample.iterrows():
        la, lb = build_line(by[r.line_a]), build_line(by[r.line_b])
        fa, ia = _fragment([x[:2] for x in by[r.line_a]], la.ks, r.k_a)
        fb, ib = _fragment([x[:2] for x in by[r.line_b]], lb.ks, r.k_b)
        rows.append({"id": f"q{i:03d}", "wers_a": fa, "wers_b": fb, "wymowa_a": ia, "wymowa_b": ib})
    GOLD_R.mkdir(parents=True, exist_ok=True)
    key = sample.assign(id=[x["id"] for x in rows])
    key.drop(columns=["decile"], errors="ignore").to_csv(GOLD_R / "klucz.csv", sep=";", index=False,
                                                         encoding="utf-8-sig")
    blind = pd.DataFrame(rows).assign(rym="", typ="", uwagi="")  # no score and no kind: a blind review
    blind.to_csv(GOLD_R / "do_oznaczenia.csv", sep=";", index=False, encoding="utf-8-sig")
    return len(blind)


def evaluate(write: bool = True) -> dict:
    """Best-F1 thresholds for every anchor, precision of detected rhymes, agreement on the rhyme kind."""
    import yaml

    from rapdna.rhymes.match import CONFIG
    from rapdna.validate.score import VALIDATION, auc, best_threshold, cross_validated

    key = rescore(pd.read_csv(GOLD_R / "klucz.csv", sep=";", encoding="utf-8-sig"))
    ann = pd.read_csv(GOLD_R / "do_oznaczenia.csv", sep=";", encoding="utf-8-sig")[["id", "rym", "typ"]]
    g = key.merge(ann, on="id")
    g["rym"] = pd.to_numeric(g.rym, errors="coerce").fillna(0).astype(int)
    report, th = {"n": int(len(g)), "annotator": "model"}, {}
    for anchor, x in g.groupby("anchor"):
        s, y = x.score.to_numpy(), x.rym.to_numpy()
        r = {"n": int(len(x)), "rhymes": int(y.sum()), "auc": round(auc(s, y), 3)}
        if y.sum():
            best = best_threshold(s, y)
            hit = x[x.rym == 1]  # kind agreement among all true rhymes
            r.update({"threshold": float(best.threshold), "precision": round(float(best.precision), 3),
                      "recall": round(float(best.recall), 3), "f1": round(float(best.f1), 3),
                      "cross_validated": cross_validated(s, y),
                      "kind_agreement": round(float((hit.type == hit.typ.map(TYPE_CODE)).mean()), 3)})
            th[anchor] = float(best.threshold)
        else:
            th[anchor] = float("inf")  # no true rhymes in the sample: this anchor stays out of the statistics
        report[anchor] = r
    report["clausal_end"] = end_threshold()
    th["clausal_end"] = report["clausal_end"]["threshold"]
    if write:
        CONFIG.write_text("# Thresholds of the rule-based ruler (variant R), calibrated by `rapdna calibrate-r` on the\n"
                          "# R gold set (best F1).\n"
                          + yaml.safe_dump({**th, "calibrated": True}, allow_unicode=True, sort_keys=False),
                          encoding="utf-8")
        (VALIDATION / "calibration_ruler.yaml").write_text(
            yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report


def end_threshold() -> dict:
    """Threshold for a rhyme at the end of both lines: the R score on the end pairs of the old gold set."""
    from rapdna.rhymes.match import pair_score
    from rapdna.validate.gold import GOLD
    from rapdna.validate.score import annotations, auc, best_threshold, cross_validated

    gold = pd.read_csv(GOLD / "rymy_klucz.csv", sep=";", encoding="utf-8-sig").merge(annotations()["model"], on="id")
    gold = gold[gold.kind == "end"]
    by = _lines(set(gold.line_a) | set(gold.line_b))
    gold = gold[gold.line_a.isin(by) & gold.line_b.isin(by)]
    s = gold.apply(lambda r: pair_score(by[r.line_a], int(r.word_a), by[r.line_b], int(r.word_b)), axis=1).to_numpy()
    y = gold.rhyme.to_numpy()
    best = best_threshold(s, y)
    return {"n": int(len(gold)), "auc": round(auc(s, y), 3), "threshold": float(best.threshold),
            "precision": round(float(best.precision), 3), "recall": round(float(best.recall), 3),
            "f1": round(float(best.f1), 3), "cross_validated": cross_validated(s, y)}


def rescore(key: pd.DataFrame) -> pd.DataFrame:
    """Score and kind computed by the current code (not saved at sampling time): the best candidate with the same
    anchor and the same end on both sides. No such candidate = score −99 (the code no longer finds it)."""
    from rapdna.rhymes.match import describe, find

    by = _lines(set(key.line_a) | set(key.line_b))
    scores, types = [], []
    for r in key.itertuples():
        a, b = by[r.line_a], by[r.line_b]
        ka = [int(x) for x in str(r.k_a).strip("[]").split()]
        kb = [int(x) for x in str(r.k_b).strip("[]").split()]
        ms = [m for m in find(a, b, same=(r.line_a == r.line_b))
              if m.anchor == r.anchor and m.i1 == ka[1] and m.j1 == kb[1]]
        best = max(ms, key=lambda m: m.score) if ms else None
        scores.append(best.score if best else -99.0)
        types.append(describe(a, b, best)["type"] if best else r.type)
    return key.assign(score=scores, type=types)
