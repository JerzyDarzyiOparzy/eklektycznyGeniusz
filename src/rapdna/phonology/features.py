"""Phonetic features of phonemes from PanPhon and the phoneme similarity matrix (the basis for rhyme and alliteration
similarity).

The feature table is read straight from PanPhon's ipa_all.csv as UTF-8, because on Windows FeatureTable opens it in
the system encoding. Similarity = 1 − weighted feature distance (PanPhon weights), on a 0–1 scale.
"""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

import panphon

DATA = Path(panphon.__file__).parent / "data"

# Polish phoneme inventory in the project's notation (see rhymes.patterns.normalize_ipa)
POLISH = ["a", "ɛ", "i", "ɔ", "u", "ɨ", "ɛ̃", "ɔ̃",
          "p", "b", "t", "d", "k", "ɡ", "c", "ɟ", "f", "v", "s", "z", "ʂ", "ʐ", "ɕ", "ʑ", "x",
          "t͡s", "d͡z", "t͡ʂ", "d͡ʐ", "t͡ɕ", "d͡ʑ", "m", "n", "ɲ", "ŋ", "l", "r", "j", "w"]

# the affricates „cz/dż” are missing from PanPhon: built from „sz/ż” plus a stop with delayed release
DERIVED = {"t͡ʂ": ("ʂ", {"cont": -1, "delrel": 1}), "d͡ʐ": ("ʐ", {"cont": -1, "delrel": 1})}


@lru_cache(maxsize=1)
def table() -> tuple[pd.DataFrame, np.ndarray]:
    df = pd.read_csv(DATA / "ipa_all.csv", encoding="utf-8").drop_duplicates("ipa").set_index("ipa")
    df = df.replace({"+": 1, "-": -1, "0": 0}).astype(int)
    weights = pd.read_csv(DATA / "feature_weights.csv", encoding="utf-8").iloc[0]
    cols = [c for c in df.columns if c in weights.index]
    return df[cols], weights[cols].to_numpy(dtype=float)


def names() -> list[str]:
    return list(table()[0].columns)


@lru_cache(maxsize=None)
def vector(seg: str) -> np.ndarray | None:
    df, _ = table()
    if seg in df.index:
        return df.loc[seg].to_numpy(dtype=float)
    if seg in DERIVED:
        base, changes = DERIVED[seg]
        v = df.loc[base].copy()
        for k, val in changes.items():
            v[k] = val
        return v.to_numpy(dtype=float)
    return None


def is_vowel(seg: str) -> bool:
    v = vector(seg)
    return v is not None and v[names().index("syl")] == 1


@lru_cache(maxsize=None)
def similarity(a: str, b: str) -> float:
    """1 − weighted PanPhon feature distance (0 = completely different, 1 = identical)."""
    if a == b:
        return 1.0
    va, vb = vector(a), vector(b)
    if va is None or vb is None:
        return 0.0
    _, w = table()
    return float(1 - (w * np.abs(va - vb)).sum() / (2 * w.sum()))


def similarity_matrix(segs: list[str] = POLISH) -> pd.DataFrame:
    return pd.DataFrame([[round(similarity(a, b), 3) for b in segs] for a in segs], index=segs, columns=segs)
