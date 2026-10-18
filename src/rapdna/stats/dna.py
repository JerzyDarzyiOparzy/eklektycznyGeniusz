"""Rapper DNA: statistics normalised within the corpus (z-score and percentile) and rapper similarity."""
import numpy as np
import pandas as pd


def normalize(stats: pd.DataFrame, keys: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    x = stats.set_index("artist")[keys].astype(float)
    z = (x - x.mean()) / x.std(ddof=0).replace(0, np.nan)
    pct = x.rank(pct=True, method="average") * 100
    return z.round(3), pct.round(1)


def similarity(z: pd.DataFrame) -> pd.DataFrame:
    """Cosine similarity of z-score vectors (1 = identical profile, -1 = opposite)."""
    m = z.fillna(0).to_numpy()
    norm = np.linalg.norm(m, axis=1, keepdims=True)
    norm[norm == 0] = 1
    u = m / norm
    return pd.DataFrame(u @ u.T, index=z.index, columns=z.index).round(3)
