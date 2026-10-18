"""Comparison of rhyme-marking methods on the reference annotations: feet.py, the probability model, line pairs.

Two levels:
1. **Syllables** (is this syllable marked): measures from `rhyme_eval.score`, separately for development and test
   songs (every other song alphabetically; the constants of `experiments/line_pairs.py` were tuned on the development
   songs). The probability model uses weights from all songs here (optimistic); its leave-one-song-out scores are in
   `config/rhyme_probability.yaml`.
2. **Whole verse**: for every section, the share of marked syllables and the mean number of marked syllables per pair
   of neighbouring lines; agreement with the reference = Spearman rank correlation over the sections.

Usage: python -m rapdna.validate.compare_methods
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from rapdna.experiments import feet, line_pairs, probability
from rapdna.validate.rhyme_eval import gold_sections, score


def verse_scores(lines, syl: set) -> dict:
    n = sum(len(line.ks) for line in lines)
    per_line = [sum((li, k) in syl for k in range(len(line.ks))) for li, line in enumerate(lines)]
    pairs_ = [min(a, b) for a, b in zip(per_line, per_line[1:])]
    return {"share": len(syl) / max(n, 1), "per_pair": float(np.mean(pairs_)) if pairs_ else 0.0}


def run():
    secs = gold_sections()
    titles = sorted({s["title"] for s in secs})
    dev = set(titles[0::2])
    methods = {
        "feet": lambda s: feet.mark(s["lines"]),
        "probability": lambda s: [(c, g) for c, g, _ in probability.mark(s["lines"])],
        "line_pairs": lambda s: line_pairs.mark(s["lines"]),
    }
    rows, verse = [], []
    marked = {name: [f(s) for s in secs] for name, f in methods.items()}
    for name in methods:
        for part, sel in (("development", lambda s: s["title"] in dev), ("test", lambda s: s["title"] not in dev),
                          ("all", lambda s: True)):
            idx = [i for i, s in enumerate(secs) if sel(s)]
            rows.append({"method": name, "songs": part, **score([secs[i] for i in idx], [marked[name][i] for i in idx])})
    for i, s in enumerate(secs):
        g = verse_scores(s["lines"], set(s["gold"]))
        row = {"song": s["title"], "reference_share": g["share"], "reference_per_pair": g["per_pair"]}
        for name in methods:
            a = verse_scores(s["lines"], {(c.line, k) for c, _ in marked[name][i] for k in range(c.start, c.end)})
            row[f"{name}_share"], row[f"{name}_per_pair"] = a["share"], a["per_pair"]
        verse.append(row)
    df, vd = pd.DataFrame(rows), pd.DataFrame(verse)
    print(df[["method", "songs", "syllables_P", "syllables_R", "syllables_F1", "end_P", "end_R", "internal_P",
              "internal_R", "pairs_P", "pairs_R"]].to_string(index=False))
    print(f"\nWhole verse: Spearman correlation with the reference ({len(secs)} sections):")
    for name in methods:
        r1 = spearmanr(vd.reference_share, vd[f"{name}_share"]).statistic
        r2 = spearmanr(vd.reference_per_pair, vd[f"{name}_per_pair"]).statistic
        print(f"  {name:12s} share of marked syllables: {r1:.2f}   marked syllables per line pair: {r2:.2f}")
    return df, vd


if __name__ == "__main__":
    run()
