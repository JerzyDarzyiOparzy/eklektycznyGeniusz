"""Rhyme scoring after Hirjee & Brown (2010, „Using Automated Rhyme Detection to Characterize Rhyming Style in Rap
Music”), adapted to Polish stress. Kept as a baseline: the statistics use rule-based end rhymes (rhymes/end.py).

1. Rhyme tail = syllables from the stressed syllable of the last word to the end (without that syllable's onset).
2. The syllables of two tails are aligned position by position. Every vowel pair and consonant pair (clusters between
   vowels, aligned from the right) gets a log-odds score:
       LO(x, y) = log2 P(x, y | rhyming pairs) − log2 P(x, y | random pairs)
   i.e. „how many times more often this pair occurs in rhymes than by chance”.
3. Rhyming pairs are learned from the corpus without labels: candidates = tails of nearby lines (1–2 lines apart),
   background = tails of lines from different songs. After the first pass only candidates with a positive score are
   kept and the tables are recomputed (a few iterations), as in the original method.
4. For rare pairs (little data) the score is pulled towards a value from PanPhon feature similarity.
The rhyme / no rhyme threshold is calibrated on labelled pairs (validate/score.py).
"""
import json
import math
import random
from collections import Counter
from dataclasses import dataclass

from rapdna import paths
from rapdna.phonology.features import similarity
from rapdna.phonology.syllables import Syllable, stressed_index, syllabify

MODEL_FILE = paths.DATA / "rhyme_model.json"
GAP = "∅"
EXTRA_SYLLABLE_PENALTY = -2.0  # tails with a different number of syllables after the stress
PRIOR_WEIGHT = 20.0  # how many „virtual observations” the PanPhon value weighs for rare pairs


@dataclass
class Tail:
    """Rhyme tail: syllables from the stress to the end + all syllables of the line/word (to extend the rhyme back)."""
    sylls: tuple[Syllable, ...]  # all syllables (of the line or word)
    words: tuple[str, ...]  # word form of every syllable (to stop at identical words)
    start: int  # index of the stressed syllable of the last word

    @property
    def rhyme(self) -> tuple[Syllable, ...]:
        return self.sylls[self.start:]

    @property
    def phones(self) -> tuple[str, ...]:
        r = self.rhyme
        out = [r[0].nucleus, *r[0].coda]
        for s in r[1:]:
            out += [*s.onset, s.nucleus, *s.coda]
        return tuple(out)

    @property
    def vowels(self) -> tuple[str, ...]:
        return tuple(s.nucleus for s in self.rhyme)


def make_tail(words: list[tuple[str, str]]) -> Tail | None:
    """words: (form, ipa) of the words of a line (or one word). The rhyme starts at the stress of the last voiced word."""
    sylls, forms, last_start = [], [], None
    for form, ipa in words:
        ws = syllabify(ipa) if ipa else ()
        if ws:
            last_start = len(sylls) + stressed_index(ws)
            sylls.extend(ws)
            forms.extend([form.lower()] * len(ws))
    if last_start is None:
        return None
    return Tail(tuple(sylls), tuple(forms), last_start)


def _clusters(rhyme: tuple[Syllable, ...]) -> list[tuple[str, ...]]:
    """Consonants after every vowel of the tail: coda + onset of the next syllable (for the last one: the coda)."""
    out = []
    for i, s in enumerate(rhyme):
        nxt = rhyme[i + 1].onset if i + 1 < len(rhyme) else ()
        out.append((*s.coda, *nxt))
    return out


def _align_right(a: tuple[str, ...], b: tuple[str, ...]) -> list[tuple[str, str]]:
    n = max(len(a), len(b))
    a2 = (GAP,) * (n - len(a)) + a
    b2 = (GAP,) * (n - len(b)) + b
    return list(zip(a2, b2))


def pair_events(t1: Tail, t2: Tail) -> tuple[list[tuple[str, str]], list[tuple[str, str]], int]:
    """(vowel pairs, consonant pairs, number of extra syllables) for two tails."""
    r1, r2 = t1.rhyme, t2.rhyme
    n = min(len(r1), len(r2))
    vowels = [(r1[i].nucleus, r2[i].nucleus) for i in range(n)]
    c1, c2 = _clusters(r1[:n]), _clusters(r2[:n])
    cons = [p for x, y in zip(c1, c2) for p in _align_right(x, y)]
    return vowels, cons, abs(len(r1) - len(r2))


def _key(x: str, y: str) -> str:
    return "|".join(sorted((x, y)))


class RhymeModel:
    def __init__(self, vowel_lo: dict[str, float], cons_lo: dict[str, float]):
        self.vowel_lo, self.cons_lo = vowel_lo, cons_lo

    # --- scoring ---
    def lo_vowel(self, x: str, y: str) -> float:
        return self.vowel_lo.get(_key(x, y), self._prior(x, y))

    def lo_cons(self, x: str, y: str) -> float:
        return self.cons_lo.get(_key(x, y), self._prior(x, y))

    @staticmethod
    def _prior(x: str, y: str) -> float:
        # no data: PanPhon similarity rescaled to log-odds (identical ≈ +2, very different ≈ −2)
        if GAP in (x, y):
            return -1.0
        return 4 * similarity(x, y) - 2 if x != y else 2.0

    def score(self, t1: Tail, t2: Tail) -> float:
        vowels, cons, extra = pair_events(t1, t2)
        return (sum(self.lo_vowel(*p) for p in vowels) + sum(self.lo_cons(*p) for p in cons)
                + EXTRA_SYLLABLE_PENALTY * extra)

    def length(self, t1: Tail, t2: Tail) -> int:
        """Rhyme length in syllables: aligned tail syllables + matching (LO > 0) vowels backwards, also across word
        boundaries, up to the first mismatching vowel or identical word."""
        n = min(len(t1.rhyme), len(t2.rhyme))
        i, j = t1.start - 1, t2.start - 1
        while i >= 0 and j >= 0:
            if t1.words[i] == t2.words[j] or self.lo_vowel(t1.sylls[i].nucleus, t2.sylls[j].nucleus) <= 0:
                break
            n += 1
            i -= 1
            j -= 1
        return n

    # --- save / load ---
    def save(self, meta: dict) -> None:
        MODEL_FILE.write_text(json.dumps({"meta": meta, "vowel_lo": self.vowel_lo, "cons_lo": self.cons_lo},
                                         ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls) -> "RhymeModel":
        d = json.loads(MODEL_FILE.read_text(encoding="utf-8"))
        return cls(d["vowel_lo"], d["cons_lo"])


def _lo_table(cand: Counter, rand: Counter) -> dict[str, float]:
    """Smoothed log-odds: with few observations the score is pulled towards the PanPhon value."""
    nc, nr = sum(cand.values()), sum(rand.values())
    out = {}
    for k in set(cand) | set(rand):
        x, y = k.split("|")
        prior = RhymeModel._prior(x, y)
        c, r = cand[k], rand[k]
        raw = math.log2((c + 0.5) / nc) - math.log2((r + 0.5) / nr)
        w = (c + r) / (c + r + PRIOR_WEIGHT)
        out[k] = round(w * raw + (1 - w) * prior, 3)
    return out


def _count(pairs: list[tuple[Tail, Tail]]) -> tuple[Counter, Counter]:
    v, c = Counter(), Counter()
    for t1, t2 in pairs:
        vowels, cons, _ = pair_events(t1, t2)
        v.update(_key(*p) for p in vowels)
        c.update(_key(*p) for p in cons)
    return v, c


def training_pairs(sections: list[list[Tail | None]], seed: int = 2026) -> tuple[list, list]:
    """(candidates: tails of lines 1–2 apart, background: random pairs of tails from different sections)."""
    rng = random.Random(seed)
    cand = [(sec[i], sec[j]) for sec in sections for i in range(len(sec)) for j in (i - 1, i - 2)
            if j >= 0 and sec[i] and sec[j]]
    flat = [(si, t) for si, sec in enumerate(sections) for t in sec if t]
    rand = []
    for _ in range(len(cand)):
        (s1, a), (s2, b) = rng.choice(flat), rng.choice(flat)
        if s1 != s2:
            rand.append((a, b))
    return cand, rand


def train(sections: list[list[Tail | None]], iterations: int = 3, seed: int = 2026, log=print) -> RhymeModel:
    """sections: line tails in consecutive sections (all rappers)."""
    cand, rand = training_pairs(sections, seed)
    rv, rc = _count(rand)
    cv, cc = _count(cand)
    model = RhymeModel(_lo_table(cv, rv), _lo_table(cc, rc))
    for it in range(iterations):
        kept = [p for p in cand if model.score(*p) > 0]
        cv, cc = _count(kept)
        model = RhymeModel(_lo_table(cv, rv), _lo_table(cc, rc))
        log(f"  iteration {it + 1}: {len(kept)}/{len(cand)} candidates taken as rhymes")
    model.save({"candidates": len(cand), "random": len(rand), "iterations": iterations})
    return model
