"""Scoring the Hirjee & Brown baseline and the figure detectors on the gold set: precision, recall, F1, AUC, threshold
calibration and inter-annotator agreement (Cohen's kappa). Labels: data/validation/gold/rymy_do_oznaczenia_<who>.csv
(column `rym` = 0/1).

The sample is drawn evenly from every score decile (deciles have equal sizes), so it is uniform over the whole
candidate population and the figures can be read as estimates for the corpus.
"""
import numpy as np
import pandas as pd
import yaml

from rapdna import paths
from rapdna.rhymes.hb_detect import THRESHOLDS
from rapdna.validate.gold import GOLD, SHEET_FIGURES

VALIDATION = paths.DATA / "validation"


def annotations() -> dict[str, pd.DataFrame]:
    out = {}
    for f in sorted(GOLD.glob("rymy_do_oznaczenia_*.csv")):
        who = f.stem.split("_")[-1]
        df = pd.read_csv(f, sep=";", encoding="utf-8-sig")
        df = df[pd.to_numeric(df.rym, errors="coerce").notna()]
        out[who] = df.assign(rhyme=df.rym.astype(int))[["id", "rhyme"]]
    return out


def _reference(ann: dict, reference: str | None) -> str:
    """The author's labels („ty”) when they exist, otherwise any available labels (e.g. „model”, a language model)."""
    return reference or ("ty" if "ty" in ann else sorted(ann)[0])


def cohen_kappa(a: pd.Series, b: pd.Series) -> float:
    po = (a == b).mean()
    pe = sum((a == v).mean() * (b == v).mean() for v in (0, 1))
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def auc(scores: np.ndarray, y: np.ndarray) -> float:
    pos, neg = scores[y == 1], scores[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([(p > neg).mean() + 0.5 * (p == neg).mean() for p in pos]))


def sweep(scores: np.ndarray, y: np.ndarray) -> pd.DataFrame:
    rows = []
    for t in np.unique(np.round(scores, 1)):
        pred = scores >= t
        tp, fp, fn = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum()), int((~pred & (y == 1)).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        rows.append({"threshold": float(t), "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
                     "tp": tp, "fp": fp, "fn": fn})
    return pd.DataFrame(rows)


def best_threshold(scores: np.ndarray, y: np.ndarray) -> pd.Series:
    return sweep(scores, y).sort_values(["f1", "precision"], ascending=False).iloc[0]


def cross_validated(scores: np.ndarray, y: np.ndarray, folds: int = 5, seed: int = 2026) -> dict:
    """The threshold is chosen on (folds−1)/folds of the data and scored on the rest: an honest estimate."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    pred = np.zeros(len(y), dtype=bool)
    for k in range(folds):
        test = idx[k::folds]
        train = np.setdiff1d(idx, test)
        t = best_threshold(scores[train], y[train]).threshold
        pred[test] = scores[test] >= t
    tp, fp, fn = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum()), int((~pred & (y == 1)).sum())
    p, r = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(2 * p * r / max(p + r, 1e-9), 3)}


def rescore(scorers: dict, reference: str | None = None) -> pd.DataFrame:
    """The gold set with scores recomputed (not the ones saved when it was drawn) for every model in `scorers`
    (name → function (tail, tail) → score). Pairs from lines no longer in the corpus are skipped."""
    from rapdna.rhymes.hb import make_tail

    ann = annotations()
    gold = pd.read_csv(GOLD / "rymy_klucz.csv", sep=";", encoding="utf-8-sig").merge(ann[_reference(ann, reference)],
                                                                                     on="id")
    w = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["line_uid", "w", "form", "ipa"])
    by_line = {u: list(zip(g.form, g.ipa)) for u, g in w.sort_values("w").groupby("line_uid", sort=False)}
    gold = gold[gold.line_a.isin(by_line) & gold.line_b.isin(by_line)].reset_index(drop=True)
    tails = [(make_tail(by_line[a][:int(i) + 1]), make_tail(by_line[b][:int(j) + 1]))
             for a, i, b, j in zip(gold.line_a, gold.word_a, gold.line_b, gold.word_b)]
    for name, fn in scorers.items():
        gold[name] = [fn(t1, t2) for t1, t2 in tails]
    return gold


def compare(gold: pd.DataFrame, names: list[str]) -> dict:
    """AUC, the best threshold and cross-validation for every model, separately for end and internal rhymes."""
    out = {}
    for kind in ("end", "internal"):
        g = gold[gold.kind == kind]
        y = g.rhyme.to_numpy()
        for name in names:
            s = g[name].to_numpy()
            best = best_threshold(s, y)
            out.setdefault(kind, {})[name] = {
                "n": int(len(g)), "auc": round(auc(s, y), 3), "threshold": float(best.threshold),
                "f1": round(float(best.f1), 3), "cross_validated": cross_validated(s, y)}
    return out


def evaluate(reference: str | None = None, write: bool = True) -> dict:
    from rapdna.rhymes.hb import RhymeModel

    ann = annotations()
    if not ann:
        raise FileNotFoundError("No labels in data/validation/gold/rymy_do_oznaczenia_<who>.csv")
    reference = _reference(ann, reference)
    # scores from the current model: those in rymy_klucz.csv come from the model at the time the set was drawn
    gold = rescore({"score": RhymeModel.load().score}, reference)

    report = {"reference": reference, "annotators": sorted(ann), "n": int(len(gold))}
    if len(ann) >= 2:
        names = sorted(ann)
        m = ann[names[0]].merge(ann[names[1]], on="id", suffixes=("_a", "_b"))
        report["kappa"] = {f"{names[0]}–{names[1]}": round(cohen_kappa(m.rhyme_a, m.rhyme_b), 3), "n": int(len(m))}

    th = yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))
    for kind, th_key in (("end", "tau_end"), ("internal", "tau_internal")):
        g = gold[gold.kind == kind]
        s, y = g.score.to_numpy(), g.rhyme.to_numpy()
        best = best_threshold(s, y)
        report[kind] = {
            "n": int(len(g)), "rhyme_share": round(float(y.mean()), 3), "auc": round(auc(s, y), 3),
            "threshold": float(best.threshold), "precision": round(float(best.precision), 3),
            "recall": round(float(best.recall), 3), "f1": round(float(best.f1), 3),
            "tp": int(best.tp), "fp": int(best.fp), "fn": int(best.fn),
            "cross_validated": cross_validated(s, y),
            # precision at the chosen threshold by rhyme type (only pairs the model accepted)
            "precision_by_type": {t: f"{int(x.rhyme.sum())}/{len(x)}"
                                  for t, x in g[g.score >= best.threshold].groupby("type")},
        }
        th[th_key] = float(best.threshold)
    th["calibrated"] = True
    th["calibrated_on"] = f"gold set, reference: {reference}"
    if write:
        THRESHOLDS.write_text(
            "# Thresholds of the Hirjee & Brown baseline (log-odds score), calibrated by `rapdna calibrate`\n"
            "# on the gold set (best F1). Manual edits are overwritten by the next calibration.\n"
            + yaml.safe_dump(th, allow_unicode=True, sort_keys=False), encoding="utf-8")
        (VALIDATION / "calibration_hb.yaml").write_text(
            yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report


def evaluate_figures(reference: str | None = None, write: bool = True) -> dict:
    """Precision and recall of figure detection on the gold set of 500 lines (+ kappa with two annotators)."""
    files = {f.stem.split("_")[-1]: f for f in GOLD.glob("figury_do_oznaczenia_*.csv")}
    if not files:
        raise FileNotFoundError("No labels in data/validation/gold/figury_do_oznaczenia_<who>.csv")
    reference = _reference(files, reference)
    ann = {k: pd.read_csv(f, sep=";", encoding="utf-8-sig").fillna(0) for k, f in files.items()}
    key = pd.read_csv(GOLD / "figury_klucz.csv", sep=";", encoding="utf-8-sig")
    auto = pd.read_parquet(paths.PARQUET / "figures.parquet")
    g = key.merge(ann[reference], on="id").merge(auto, on="line_uid")
    report = {"reference": reference, "n": int(len(g))}
    for f, col in SHEET_FIGURES.items():
        y = pd.to_numeric(g[col], errors="coerce").fillna(0).astype(int).to_numpy()
        p = g[f].astype(bool).to_numpy()
        tp, fp, fn = int((p & (y == 1)).sum()), int((p & (y == 0)).sum()), int((~p & (y == 1)).sum())
        report[f] = {"in_gold": int(y.sum()), "detected": int(p.sum()), "tp": tp, "fp": fp, "fn": fn,
                     "precision": round(tp / (tp + fp), 3) if tp + fp else None,
                     "recall": round(tp / (tp + fn), 3) if tp + fn else None}
        if len(ann) >= 2:
            a, b = sorted(ann)[:2]
            m = ann[a][["id", col]].merge(ann[b][["id", col]], on="id")
            report[f]["kappa"] = round(cohen_kappa(m[col + "_x"].astype(int), m[col + "_y"].astype(int)), 3)
    if write:
        (VALIDATION / "figures_eval.yaml").write_text(
            yaml.safe_dump(report, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return report
