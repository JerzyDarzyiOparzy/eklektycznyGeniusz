"""Scene map (plan, phase 7): rappers and their albums on a plane by technical DNA.

Every album is a vector of DNA statistics (vocabulary is replaced by MATTR, because unique lemmas per 8,000 words
cannot be computed for short albums). Features are standardised at the album level and projected by PCA onto 2
dimensions (fixed seed); a rapper's point is the mean of their albums weighted by the number of lines. Albums with
< 150 of the rapper's lines are skipped as too small. Axes are described by the statistics with the largest loadings.
"""
import numpy as np
import pandas as pd

MIN_LINES = 150


def scene(albums: pd.DataFrame, defs: dict) -> dict:
    from sklearn.decomposition import PCA

    keys = [("mattr" if k == "vocabulary" else k) for k, d in defs.items() if d.get("dna")]
    keys = [k for k in keys if k in albums.columns]
    a = albums[albums.lines >= MIN_LINES].dropna(subset=keys).reset_index(drop=True)
    x = a[keys].astype(float)
    z = (x - x.mean()) / x.std(ddof=0).replace(0, np.nan)
    z = z.fillna(0)
    pca = PCA(n_components=2, random_state=2026)
    xy = pca.fit_transform(z.to_numpy())
    a["x"], a["y"] = xy[:, 0], xy[:, 1]
    artists = (a.assign(wx=a.x * a.lines, wy=a.y * a.lines).groupby("artist")
               .agg(wx=("wx", "sum"), wy=("wy", "sum"), w=("lines", "sum")))
    artists["x"], artists["y"] = artists.wx / artists.w, artists.wy / artists.w

    def axis(i: int) -> list[dict]:
        load = pd.Series(pca.components_[i], index=keys)
        top = load.abs().sort_values(ascending=False).head(4).index
        return [{"stat": k, "loading": round(float(load[k]), 3)} for k in top]

    return {
        "keys": keys,
        "explained": [round(float(v), 3) for v in pca.explained_variance_ratio_],
        "axes": [axis(0), axis(1)],
        "artists": [{"artist": n, "x": round(float(r.x), 3), "y": round(float(r.y), 3)} for n, r in artists.iterrows()],
        "albums": [{"artist": r.artist, "album": r.album, "year": int(r.year), "lines": int(r.lines),
                    "x": round(float(r.x), 3), "y": round(float(r.y), 3)}
                   for r in a.sort_values(["artist", "year"]).itertuples()],
    }
