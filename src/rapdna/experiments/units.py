"""Experiment: rhyme units („blocks”, docs/en/internal-rhymes.md): a vowel plus all consonants after it up to the
next vowel. „tango” → [aŋɡ] [ɔ], „bagno” → [aɡn] [ɔ]. There are as many units as syllables, but the cut falls before
the vowel, so the result does not depend on where the syllable boundary sits inside a consonant cluster.

Variant A: unit pair score = Hirjee & Brown score of their vowels and right-aligned consonants. The sum over a tail's
units equals `RhymeModel.score` exactly (tests/test_units.py).
Variant B: scores learned for whole unit pairs: rejected (worse on end rhymes, rated „kasa / kosa” a rhyme).
"""
import json
import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from rapdna import paths
from rapdna.rhymes.hb import (EXTRA_SYLLABLE_PENALTY, RhymeModel, Tail, _align_right, _clusters, _key, make_tail,
                              training_pairs)

OUT = paths.DATA / "rhyme_units"


@dataclass(frozen=True)
class Unit:
    vowel: str
    cons: tuple[str, ...]

    def __str__(self) -> str:
        return self.vowel + "".join(self.cons)


def units(tail: Tail, n: int | None = None) -> tuple[Unit, ...]:
    """Units of a rhyme tail (from the stressed vowel). With `n`, only the first n units, the last one without the
    consonants that open the next syllable: this is how the model compares tails of different lengths."""
    r = tail.rhyme if n is None else tail.rhyme[:n]
    return tuple(Unit(s.nucleus, c) for s, c in zip(r, _clusters(r)))


def rhyme_units(words: list[tuple[str, str]]) -> tuple[Unit, ...]:
    """(form, ipa) of the words of a line or of one word → units of the rhyme tail."""
    t = make_tail(words)
    return units(t) if t else ()


def unit_score(model: RhymeModel, a: Unit, b: Unit) -> float:
    return model.lo_vowel(a.vowel, b.vowel) + sum(model.lo_cons(x, y) for x, y in _align_right(a.cons, b.cons))


def score(model: RhymeModel, t1: Tail, t2: Tail) -> float:
    """Score of a pair of tails from their units (variant A)."""
    n = min(len(t1.rhyme), len(t2.rhyme))
    return (sum(unit_score(model, a, b) for a, b in zip(units(t1, n), units(t2, n)))
            + EXTRA_SYLLABLE_PENALTY * abs(len(t1.rhyme) - len(t2.rhyme)))


# --- variant B: scores learned for whole unit pairs ---------------------------------------------------------------

UNIT_MODEL_FILE = OUT / "unit_model.json"
PRIOR_WEIGHT = 20.0  # how many „virtual observations” the variant A score weighs for rare unit pairs


class UnitModel:
    """Unit pair score = log-odds „in rhymes / by chance” for the whole pair (e.g. aŋɡ|aɡn), pulled towards
    variant A (sum of phoneme scores) when the pair is rare. A pair never seen in the corpus simply gets variant A."""

    def __init__(self, base: RhymeModel, lo: dict[str, float]):
        self.base, self.lo = base, lo

    def pair(self, a: Unit, b: Unit) -> float:
        v = self.lo.get(_key(str(a), str(b)))
        return unit_score(self.base, a, b) if v is None else v

    def score(self, t1: Tail, t2: Tail) -> float:
        n = min(len(t1.rhyme), len(t2.rhyme))
        return (sum(self.pair(a, b) for a, b in zip(units(t1, n), units(t2, n)))
                + EXTRA_SYLLABLE_PENALTY * abs(len(t1.rhyme) - len(t2.rhyme)))

    def save(self, meta: dict) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        UNIT_MODEL_FILE.write_text(json.dumps({"meta": meta, "lo": self.lo}, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, base: RhymeModel) -> "UnitModel":
        return cls(base, json.loads(UNIT_MODEL_FILE.read_text(encoding="utf-8"))["lo"])


def _count_units(pairs) -> Counter:
    c: Counter = Counter()
    for t1, t2 in pairs:
        n = min(len(t1.rhyme), len(t2.rhyme))
        c.update(_key(str(a), str(b)) for a, b in zip(units(t1, n), units(t2, n)))
    return c


def _unit_lo(cand: Counter, rand: Counter, base: RhymeModel, examples: dict[str, tuple[Unit, Unit]]) -> dict[str, float]:
    nc, nr = sum(cand.values()), sum(rand.values())
    out = {}
    for k in set(cand) | set(rand):
        c, r = cand[k], rand[k]
        raw = math.log2((c + 0.5) / nc) - math.log2((r + 0.5) / nr)
        w = (c + r) / (c + r + PRIOR_WEIGHT)
        out[k] = round(w * raw + (1 - w) * unit_score(base, *examples[k]), 3)
    return out


def train_units(sections: list, base: RhymeModel, iterations: int = 3, seed: int = 2026, log=print) -> UnitModel:
    """The same pairs as the phoneme model (nearby lines vs random), counted on unit pairs. Starts from variant A."""
    cand, rand = training_pairs(sections, seed)
    examples = {}
    for t1, t2 in cand + rand:
        n = min(len(t1.rhyme), len(t2.rhyme))
        for a, b in zip(units(t1, n), units(t2, n)):
            examples.setdefault(_key(str(a), str(b)), (a, b))
    rc = _count_units(rand)
    model = UnitModel(base, {})
    for it in range(iterations):
        kept = [p for p in cand if model.score(*p) > 0]
        model = UnitModel(base, _unit_lo(_count_units(kept), rc, base, examples))
        log(f"  iteration {it + 1}: {len(kept)}/{len(cand)} candidates taken as rhymes, unit pairs: {len(model.lo)}")
    model.save({"candidates": len(cand), "random": len(rand), "iterations": iterations, "prior_weight": PRIOR_WEIGHT})
    return model


def corpus_units(words) -> Counter:
    """Units from the rhyme tails of all word occurrences (words: DataFrame with columns form, ipa)."""
    c: Counter = Counter()
    for form, ipa in zip(words.form, words.ipa):
        if ipa:
            c.update(rhyme_units([(form, ipa)]))
    return c


def unit_examples(words, k: int = 3) -> dict[Unit, list[str]]:
    """The most frequent words in which the unit is the stressed unit (for checking by ear)."""
    c: dict[Unit, Counter] = {}
    for form, ipa in zip(words.form.str.lower(), words.ipa):
        us = rhyme_units([(form, ipa)]) if ipa else ()
        if us:
            c.setdefault(us[0], Counter())[form] += 1
    return {u: [f for f, _ in cnt.most_common(k)] for u, cnt in c.items()}


def neighbors(us: list[Unit], m: np.ndarray, counts: Counter, i: int, k: int = 5, min_n: int = 20) -> list[int]:
    """The k units that rhyme best with unit i (excluding itself), among units with ≥ min_n occurrences."""
    ok = np.array([counts[u] >= min_n for u in us])
    ok[i] = False
    order = np.argsort(-m[i])
    return [int(j) for j in order if ok[j]][:k]


def project(m: np.ndarray, n: int, seed: int = 2026) -> np.ndarray:
    """Projection of the n most frequent units onto a plane (for viewing only). Distance from scores as from a dot
    product: d² = s(a,a) + s(b,b) − 2·s(a,b), so a unit sits close to those it rhymes with almost as well as itself."""
    from sklearn.manifold import MDS

    s = m[:n, :n].astype(float)
    d = np.sqrt(np.maximum(0, np.diag(s)[:, None] + np.diag(s)[None, :] - 2 * s))
    return MDS(n_components=2, metric="precomputed", init="random", random_state=seed, n_init=4).fit_transform(d)


def build_matrix(model: RhymeModel, counts: Counter, log=print) -> tuple[list[Unit], np.ndarray]:
    """Score matrix of all unit pairs in the corpus (most frequent first) → data/rhyme_units/."""
    us = [u for u, _ in counts.most_common()]
    m = np.zeros((len(us), len(us)), dtype=np.float32)
    for i, a in enumerate(us):
        for j in range(i, len(us)):
            m[i, j] = m[j, i] = unit_score(model, a, us[j])
    OUT.mkdir(parents=True, exist_ok=True)
    np.save(OUT / "scores.npy", m)
    (OUT / "units.json").write_text(json.dumps(
        [{"unit": str(u), "vowel": u.vowel, "cons": list(u.cons), "n": counts[u]} for u in us], ensure_ascii=False),
        encoding="utf-8")
    log(f"units: {len(us)}, matrix {m.shape[0]}×{m.shape[1]}")
    return us, m
