"""Cue weights of the rhyme probability experiment (`experiments/probability.py`), fitted to the reference rhyme
annotations, never to the corpus lyrics.

Training unit: a candidate cell; label: at least half of its syllables are marked in the reference.
Scoring: leave one song out, with weights fitted on the other songs, scored on the held-out one, for every song in turn.
Measures as in `rhyme_eval.score`, compared with `feet.py`. Finally, weights from all songs →
`config/rhyme_probability.yaml`.

Usage: python -m rapdna.validate.train_probability
"""
import numpy as np
import pandas as pd
import yaml

from rapdna.experiments import feet, probability
from rapdna.validate.rhyme_eval import gold_sections, score

THRESHOLDS = [round(float(x), 2) for x in np.arange(0.2, 0.75, 0.05)]


def dataset(use_meter: bool) -> list[dict]:
    """Scored sections with cell features and labels (with a recording: only songs that have one)."""
    out = gold_sections(meter=use_meter)
    for s in out:
        s["feats"] = probability.features(s["lines"], s["meter"])
        s["labels"] = [sum((c.line, k) in s["gold"] for k in range(c.start, c.end)) / (c.end - c.start) >= 0.5
                       for c, _ in s["feats"]]
    return out


def fit(secs: list[dict]) -> dict:
    from sklearn.linear_model import LogisticRegression

    names = sorted({k for s in secs for _, f in s["feats"] for k in f})
    X = np.array([[f.get(n, 0.0) for n in names] for s in secs for _, f in s["feats"]])
    y = np.array([lab for s in secs for lab in s["labels"]])
    m = LogisticRegression(C=1.0, max_iter=5000).fit(X, y)
    w = {n: round(float(c), 3) for n, c in zip(names, m.coef_[0])}
    w["intercept"] = round(float(m.intercept_[0]), 3)
    return w


def cross_validate(secs: list[dict]) -> tuple[pd.DataFrame, dict]:
    """Leave one song out: scores for every threshold (summed over all songs) and feet.py on the same sections."""
    marked = {th: [None] * len(secs) for th in THRESHOLDS}
    for title in sorted({s["title"] for s in secs}):
        cfg = {"weights": fit([s for s in secs if s["title"] != title]), "threshold": 0.5}
        for i, s in enumerate(secs):
            if s["title"] == title:
                for th in THRESHOLDS:
                    marked[th][i] = [(c, g) for c, g, _ in probability.mark(s["lines"], s["meter"], cfg, th)]
    rows = [{"threshold": th, **score(secs, marked[th])} for th in THRESHOLDS]
    return pd.DataFrame(rows), score(secs, [feet.mark(s["lines"]) for s in secs])


def _best(cv: pd.DataFrame) -> dict:
    return {k: float(v) for k, v in cv.loc[cv.syllables_F1.idxmax()].items()}


def run():
    text = dataset(False)
    cv_text, base = cross_validate(text)
    print("feet.py:", base)
    print(cv_text.to_string(index=False))
    cfg = {"description": "Cue weights of the rhyme probability experiment (experiments/probability.py), fitted to the "
                          "reference rhyme annotations (validate/train_probability.py). Generated, do not edit by hand.",
           "data": f"{len({s['title'] for s in text})} songs, {len(text)} sections, "
                   f"{sum(len(s['labels']) for s in text)} cells",
           "threshold": _best(cv_text)["threshold"], "weights": fit(text),
           "validation_leave_one_song_out": _best(cv_text), "feet_for_comparison": base}
    audio = dataset(True)
    if audio:
        titles = sorted({s["title"] for s in audio})
        cv_sub, base_sub = cross_validate([s for s in text if s["title"] in titles])
        cv_audio, _ = cross_validate(audio)
        print(f"\nSongs with a recording ({len(titles)}): feet.py:", base_sub)
        print("without the recording:\n", cv_sub.to_string(index=False))
        print("with the recording:\n", cv_audio.to_string(index=False))
        cfg.update({"threshold_with_audio": _best(cv_audio)["threshold"], "weights_with_audio": fit(audio),
                    "validation_with_audio": _best(cv_audio),
                    "validation_same_songs_without_audio": _best(cv_sub),
                    "feet_same_songs": base_sub, "songs_with_audio": titles})
    probability.CONFIG.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("Saved", probability.CONFIG)


if __name__ == "__main__":
    run()
