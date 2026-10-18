"""Rapper profiles: what sets each rapper apart from the rest of the corpus (docs/en/reliability.md).

For every feature in `config/profile.yaml`:
1. the rapper's value is the word-weighted mean over their songs (songs with ≥ 24 own lines);
2. robust z-score against the other rappers: (value − median) / (1.4826 · MAD);
3. a 95% interval from resampling the rapper's songs (bootstrap, B draws);
4. reliability of the rapper's mean from the rapper-vs-song ICC (`stats/reliability.py`) and their number of songs:
   n·ICC / (1 + (n − 1)·ICC).
A feature becomes a **distinguishing trait** when |z| ≥ MIN_Z, the interval stays on one side of the corpus
median and reliability ≥ MIN_RELIABILITY. At most MAX_PER_DIMENSION traits per style dimension, so that one
dimension (e.g. rhymes) cannot fill the whole profile.

Usage: python -m rapdna.stats.profile → data/stats/profiles.json
"""
import json

import numpy as np
import pandas as pd
import yaml

from rapdna import paths
from rapdna.stats.reliability import icc

CONFIG = paths.CONFIG / "profile.yaml"
STATS = paths.DATA / "stats"
SOURCES = {"songs_technical": "song_features.parquet", "songs_surface": "surface_features_songs.parquet",
           "songs_text": "text_features_songs.parquet"}
MIN_LINES = 24
B = 1000
SEED = 2026
MIN_Z = 1.0
MIN_RELIABILITY = 0.8
MAX_TRAITS = 5
MAX_PER_DIMENSION = 2


def load_songs() -> pd.DataFrame:
    """One row per song with all per-song features and the rapper's word count as weight."""
    tech = pd.read_parquet(STATS / SOURCES["songs_technical"])
    out = tech.rename(columns={"words": "weight"})
    for src in ("songs_surface", "songs_text"):
        df = pd.read_parquet(STATS / SOURCES[src])
        df = df.drop(columns=[c for c in ("artist", "year", "album", "words", "lines", "rapper_words") if c in df])
        out = out.merge(df, on="song_id", how="left")
    return out


def weighted(values: np.ndarray, weights: np.ndarray) -> float:
    ok = ~np.isnan(values)
    return float(np.average(values[ok], weights=weights[ok])) if ok.any() else float("nan")


def feature_table(songs: pd.DataFrame, column: str, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    x_all, g_all = songs[column].to_numpy(float), songs.artist.to_numpy()
    feature_icc = icc(x_all, g_all)
    for artist, g in songs.groupby("artist"):
        x, w = g[column].to_numpy(float), g.weight.to_numpy(float)
        idx = rng.integers(0, len(g), size=(B, len(g)))
        boot = np.array([weighted(x[i], w[i]) for i in idx])
        n = int((~np.isnan(x)).sum())
        rel = n * feature_icc / (1 + (n - 1) * feature_icc) if feature_icc > 0 else 0.0
        rows.append({"artist": artist, "value": weighted(x, w), "lo": np.nanpercentile(boot, 2.5),
                     "hi": np.nanpercentile(boot, 97.5), "songs": n, "reliability": rel})
    t = pd.DataFrame(rows)
    med = t.value.median()
    mad = 1.4826 * (t.value - med).abs().median()
    t["z"] = (t.value - med) / mad if mad > 0 else 0.0
    t["rank"] = t.value.rank(ascending=False, method="min").astype(int)
    t["median"] = med
    t["icc"] = feature_icc
    return t


def build() -> dict:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))["features"]
    songs = load_songs()
    songs = songs[songs.lines >= MIN_LINES]
    rng = np.random.default_rng(SEED)
    tables = {key: feature_table(songs, f["column"], rng) for key, f in cfg.items() if f["column"] in songs}
    artists = sorted(songs.artist.unique())
    n_artists = len(artists)
    profiles = {}
    for a in artists:
        feats = {}
        for key, t in tables.items():
            r = t[t.artist == a].iloc[0]
            side = "high" if r.z > 0 else "low"
            clear = (r.lo > r["median"]) if side == "high" else (r.hi < r["median"])
            feats[key] = {"value": r.value, "lo": r.lo, "hi": r.hi, "z": r.z, "rank": int(r["rank"]),
                          "median": r["median"], "reliability": r.reliability,
                          "trait": bool(abs(r.z) >= MIN_Z and clear and r.reliability >= MIN_RELIABILITY),
                          "side": side}
        ranked = sorted((k for k, v in feats.items() if v["trait"]), key=lambda k: -abs(feats[k]["z"]))
        traits, per_dim = [], {}
        for k in ranked:
            d = cfg[k]["dimension"]
            if per_dim.get(d, 0) < MAX_PER_DIMENSION and len(traits) < MAX_TRAITS:
                traits.append(k)
                per_dim[d] = per_dim.get(d, 0) + 1
        profiles[a] = {"songs": int((songs.artist == a).sum()), "features": feats, "traits": traits}
    meta = {k: {**{f: cfg[k].get(f) for f in ("label", "unit", "format", "dimension", "status", "note", "check", "high", "low")},
                "icc": float(tables[k].icc.iloc[0])} for k in tables}
    return {"artists": n_artists, "features": meta, "profiles": profiles}


def _clean(o):
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_clean(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return None if np.isnan(o) or np.isinf(o) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    return o


def run() -> dict:
    data = _clean(build())
    (STATS / "profiles.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


if __name__ == "__main__":
    d = run()
    for a, p in d["profiles"].items():
        print(a, "|", "; ".join(f"{d['features'][k][p['features'][k]['side']]} (z {p['features'][k]['z']:+.1f}, "
                                f"{p['features'][k]['rank']}. z {d['artists']})" for k in p["traits"]))
