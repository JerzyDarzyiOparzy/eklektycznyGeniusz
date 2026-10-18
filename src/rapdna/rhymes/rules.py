"""Rule-based ruler (variant R, docs/en/methodology.md): scores a pair of syllable units without
learning anything from the corpus.

Unit pair score = vowel score (from the definition of rhyme) + consonant score (PanPhon features, clusters aligned for
the highest sum). All constants are here and public. The ruler does not depend on the data.
"""
from functools import lru_cache

from rapdna.phonology.features import similarity

SAME = 2.0  # identical phoneme
# vowels that count as close in rhyme (docs/en/glossary.md): e/ę and o/ą: nasality fades in speech;
# i/y, the closest pair
NEAR_VOWELS = {frozenset(("ɛ", "ɛ̃")): 1.5, frozenset(("ɔ", "ɔ̃")): 1.5, frozenset(("i", "ɨ")): 1.0}
OTHER_VOWEL = -100.0  # any other vowel breaks the rhyme (by definition)
CONS_SLOPE = 8.0  # different consonants: 2 − 8·(1 − similarity); p/b → +1.8, t/k → +0.8, p/l → about −1.2
GAP = -1.0  # consonant without a counterpart


def vowel(a: str, b: str) -> float:
    if a == b:
        return SAME
    return NEAR_VOWELS.get(frozenset((a, b)), OTHER_VOWEL)


def consonant(a: str, b: str) -> float:
    return SAME if a == b else SAME - CONS_SLOPE * (1 - similarity(a, b))


@lru_cache(maxsize=None)
def cluster(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Best alignment of two consonant clusters (with gaps), as a sum of scores. Empty with empty = 0."""
    n, m = len(a), len(b)
    d = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d[i][0] = d[i - 1][0] + GAP
    for j in range(1, m + 1):
        d[0][j] = d[0][j - 1] + GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = max(d[i - 1][j - 1] + consonant(a[i - 1], b[j - 1]), d[i - 1][j] + GAP, d[i][j - 1] + GAP)
    return d[n][m]


@lru_cache(maxsize=None)
def unit(va: str, ca: tuple[str, ...], vb: str, cb: tuple[str, ...]) -> float:
    """Score of a pair of units (vowel + following consonant cluster)."""
    return vowel(va, vb) + cluster(ca, cb)
