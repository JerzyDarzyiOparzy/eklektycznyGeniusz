"""Syllabification of a word (IPA): onset, nucleus (vowel), coda, stress.

Consonants between vowels follow the maximal onset principle: the next syllable gets the longest tail of the cluster
that occurs as an onset of Polish words (list derived from the phonetic dictionary). espeak-ng puts the stress mark
ˈ (primary) or ˌ (secondary) right before the stressed vowel.
"""
import json
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

from rapdna import paths
from rapdna.phonology.features import is_vowel
from rapdna.rhymes.patterns import SECONDARY, STRESS, phonemes

ONSETS_FILE = paths.RESOURCES / "legal_onsets.json"
MIN_ONSET_COUNT = 20  # a cluster must start at least this many dictionary words


@dataclass(frozen=True)
class Syllable:
    onset: tuple[str, ...]
    nucleus: str
    coda: tuple[str, ...]
    stress: int  # 0 none, 1 primary, 2 secondary

    @property
    def rime(self) -> tuple[str, ...]:
        return (self.nucleus, *self.coda)


def build_legal_onsets() -> set[tuple[str, ...]]:
    import pandas as pd

    counts: Counter = Counter()
    for ipa in pd.read_parquet(paths.PHONETIC_DICT, columns=["ipa"]).ipa:
        ph = [p for p in phonemes(ipa) if p not in (STRESS, SECONDARY)]
        onset = []
        for p in ph:
            if is_vowel(p):
                break
            onset.append(p)
        counts[tuple(onset)] += 1
    legal = {o for o, n in counts.items() if n >= MIN_ONSET_COUNT}
    ONSETS_FILE.write_text(json.dumps(sorted(map(list, legal)), ensure_ascii=False), encoding="utf-8")
    return legal


@lru_cache(maxsize=1)
def legal_onsets() -> frozenset:
    if not ONSETS_FILE.exists():
        return frozenset(build_legal_onsets())
    return frozenset(tuple(o) for o in json.loads(ONSETS_FILE.read_text(encoding="utf-8")))


@lru_cache(maxsize=200_000)
def syllabify(ipa: str) -> tuple[Syllable, ...]:
    ph = phonemes(ipa)
    # (phoneme, stress on this vowel)
    segs, mark = [], 0
    for p in ph:
        if p == STRESS:
            mark = 1
        elif p == SECONDARY:
            mark = 2
        else:
            segs.append((p, mark if is_vowel(p) else 0))
            if is_vowel(p):
                mark = 0
    nuclei = [i for i, (p, _) in enumerate(segs) if is_vowel(p)]
    if not nuclei:
        return ()
    legal = legal_onsets()
    bounds = [0]  # start of every syllable
    for a, b in zip(nuclei, nuclei[1:]):
        cluster = [p for p, _ in segs[a + 1:b]]
        split = len(cluster)  # by default everything goes to the coda of the previous syllable
        for k in range(len(cluster) + 1):
            if tuple(cluster[k:]) in legal or k == len(cluster):
                split = k
                break
        bounds.append(a + 1 + split)
    bounds.append(len(segs))
    out = []
    for n, (start, end) in zip(nuclei, zip(bounds, bounds[1:])):
        onset = tuple(p for p, _ in segs[start:n])
        coda = tuple(p for p, _ in segs[n + 1:end])
        out.append(Syllable(onset, segs[n][0], coda, segs[n][1]))
    if not any(s.stress == 1 for s in out):  # no stress mark: Polish rule, the penultimate syllable
        i = max(0, len(out) - 2)
        out[i] = Syllable(out[i].onset, out[i].nucleus, out[i].coda, 1)
    return tuple(out)


def stressed_index(sylls: tuple[Syllable, ...]) -> int:
    """Index of the last syllable with primary stress (a rhyme starts there)."""
    idx = [i for i, s in enumerate(sylls) if s.stress == 1]
    return idx[-1] if idx else max(0, len(sylls) - 2)
