"""Sound vectors after Parrish (2017, „Poetic Sound Similarity Vectors Using Phonetic Features”).

Word → phonemes with start and end markers → for every pair of neighbouring phonemes, all pairs of their phonetic
features (PanPhon „+” features) → vector of feature-pair counts → PCA to `DIM` dimensions.
The cosine similarity of two vectors measures how alike the whole words sound (not only their endings).
"""
import numpy as np

from rapdna import paths
from rapdna.phonology.features import names, vector
from rapdna.rhymes.patterns import SECONDARY, STRESS, phonemes

DIM = 50
VEC_FILE = paths.DATA / "soundvec.npz"


def _feature_sets(ipa: str) -> list[list[str]]:
    feats = names()
    seq = [["BEG"]]
    for p in phonemes(ipa):
        if p in (STRESS, SECONDARY):
            continue
        v = vector(p)
        if v is not None:
            seq.append([f for f, x in zip(feats, v) if x == 1])
    seq.append(["END"])
    return seq


def raw_vector(ipa: str) -> np.ndarray:
    labels = names() + ["BEG", "END"]
    index = {f: i for i, f in enumerate(labels)}
    n = len(labels)
    out = np.zeros(n * n, dtype=np.float32)
    seq = _feature_sets(ipa)
    for a, b in zip(seq, seq[1:]):
        for fa in a:
            for fb in b:
                out[index[fa] * n + index[fb]] += 1
    return out


def build(words: dict[str, str]) -> tuple[list[str], np.ndarray]:
    """form → IPA; returns the forms and normalised PCA vectors (saved to data/soundvec.npz)."""
    from sklearn.decomposition import PCA

    forms = sorted(w for w, ipa in words.items() if ipa)
    raw = np.stack([raw_vector(words[w]) for w in forms])
    raw = raw / np.maximum(raw.sum(axis=1, keepdims=True), 1)
    vecs = PCA(n_components=DIM, random_state=2026).fit_transform(raw)
    vecs /= np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)
    np.savez_compressed(VEC_FILE, forms=np.array(forms), vecs=vecs.astype(np.float32))
    return forms, vecs


def load() -> dict[str, np.ndarray]:
    d = np.load(VEC_FILE)
    return dict(zip(d["forms"].tolist(), d["vecs"]))
