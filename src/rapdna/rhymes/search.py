"""„What rhymes with X” (`rapdna rhymes-for`), on the rule-based ruler (variant R).

Index: every word → its rhyme tail (units from the stressed vowel to the end of the word). Words with the same tail
share one entry, so tails are compared rather than all words. A pair of tails is scored with the same sum of unit
scores as a clausal rhyme (`rules.py`); a different number of syllables after the stress means no clausal rhyme.
"""
from collections import defaultdict

import pandas as pd

from rapdna import paths
from rapdna.rhymes import rules
from rapdna.rhymes.match import build_line


def tail(form: str, ipa: str) -> tuple:
    """Units from the stress to the word end: ((vowel, consonants), …), the last one with the consonants to the end."""
    ln = build_line([(form, ipa, form, "")])
    if not ln.ks or 0 not in ln.stress_of_word:
        return ()
    ks = ln.ks[ln.stress_of_word[0]:]
    return tuple((k.v, k.coda if i == len(ks) - 1 else k.cons) for i, k in enumerate(ks))


def tail_score(a: tuple, b: tuple) -> float:
    if len(a) != len(b):
        return float("-inf")
    return sum(rules.unit(va, ca, vb, cb) for (va, ca), (vb, cb) in zip(a, b))


class Index:
    def __init__(self, words: pd.DataFrame):
        """words: columns form, ipa (e.g. data/parquet/words.parquet or the phonetic dictionary)."""
        counts = words.assign(f=words.form.str.lower()).groupby(["f", "ipa"]).size()
        self.by_tail: dict[tuple, list[tuple[str, int]]] = defaultdict(list)
        for (form, ipa), n in counts.items():
            t = tail(form, ipa)
            if t:
                self.by_tail[t].append((form, int(n)))
        for t in self.by_tail:
            self.by_tail[t].sort(key=lambda x: -x[1])

    def rhymes(self, form: str, ipa: str, k: int = 20, per_tail: int = 3, min_score: float | None = None) -> list:
        """The best tails for a word: (score, tail, most frequent words with that tail). Only above the calibrated
        end-rhyme threshold (config/thresholds_r.yaml), i.e. rhymes only."""
        if min_score is None:
            from rapdna.rhymes.match import thresholds

            min_score = thresholds()["clausal_end"]
        t = tail(form, ipa)
        scored = [(s, u) for u in self.by_tail if len(u) == len(t) and (s := tail_score(t, u)) >= min_score]
        scored.sort(key=lambda x: -x[0])
        out = []
        for s, u in scored:
            words = [w for w, _ in self.by_tail[u] if w != form.lower()][:per_tail]
            if words:
                out.append((round(s, 2), " ".join(v + "".join(c) for v, c in u), words))
            if len(out) == k:
                break
        return out


def load_index() -> Index:
    return Index(pd.read_parquet(paths.PARQUET / "words.parquet", columns=["form", "ipa"]).dropna())
