"""Rhyme detection within a section with the Hirjee & Brown model (rhymes/hb.py). Kept as a baseline for comparison;
the statistics use rule-based end rhymes (rhymes/end.py).

- end rhyme: the line tail (from the stress of the last word) and the tail of one of the `window` previous lines;
  the best-scored partner is kept, a rhyme when the score ≥ `tau_end`;
- internal rhyme: a pair of content words in the same or the neighbouring line, at least one not at the line end;
  a rhyme when the score ≥ `tau_internal`;
- rhyme length: tail syllables + matching vowels backwards across word boundaries („polskie tango / grząskie bagno”);
- type: exact (identical phonemes from the stress), assonance (identical vowels), imperfect (the rest).
The `tau_*` thresholds are calibrated on labelled pairs (validate/score.py, config/thresholds.yaml).
"""
from dataclasses import dataclass

import yaml

from rapdna import paths
from rapdna.rhymes.density import Word
from rapdna.rhymes.hb import RhymeModel, Tail, make_tail

THRESHOLDS = paths.CONFIG / "thresholds.yaml"
TYPE_RANK = {"exact": 3, "assonance": 2, "imperfect": 1}


def thresholds() -> dict:
    return yaml.safe_load(THRESHOLDS.read_text(encoding="utf-8"))


@dataclass
class Rhyme:
    kind: str  # end | internal
    type: str  # exact | assonance | imperfect
    line_a: int
    word_a: int
    line_b: int
    word_b: int
    syllables: int
    score: float


def rhyme_type(t1: Tail, t2: Tail) -> str:
    if t1.phones == t2.phones:
        return "exact"
    if t1.vowels == t2.vowels:
        return "assonance"
    return "imperfect"


def same_stem(a: str, b: str) -> bool:
    a, b = a.lower(), b.lower()
    return a == b or (min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)))


def candidates_section(lines: list[list[Word]], model: RhymeModel, window: int = 3,
                       min_internal: float = -2.0) -> list[Rhyme]:
    """All candidate pairs with a score (no threshold for end rhymes; internal ones above `min_internal`).
    The type is always filled in; the threshold decides rhyme / no rhyme."""
    out: list[Rhyme] = []
    keys = [tuple(w.form.lower() for w in line) for line in lines]
    ends = {i: max((k for k, w in enumerate(line) if w.vowels), default=None) for i, line in enumerate(lines)}
    line_tails = {i: make_tail([(w.form, w.ipa) for w in lines[i][:ends[i] + 1]])
                  for i in ends if ends[i] is not None}

    for i in sorted(line_tails):
        for j in range(max(0, i - window), i):
            if j not in line_tails or keys[i] == keys[j]:
                continue
            if same_stem(lines[j][ends[j]].form, lines[i][ends[i]].form):
                continue
            t1, t2 = line_tails[j], line_tails[i]
            out.append(Rhyme("end", rhyme_type(t1, t2), j, ends[j], i, ends[i],
                             model.length(t1, t2), round(model.score(t1, t2), 3)))

    word_tails = {}
    for i, line in enumerate(lines):
        for k, w in enumerate(line):
            if w.vowels and not w.function:
                word_tails[(i, k)] = make_tail([(x.form, x.ipa) for x in line[:k + 1]])
    for i, line in enumerate(lines):
        cands = [(i, k) for k in range(len(line)) if (i, k) in word_tails]
        prev = ([(i - 1, k) for k in range(len(lines[i - 1])) if (i - 1, k) in word_tails]
                if i and keys[i - 1] != keys[i] else [])
        pool = prev + cands
        for x in range(len(pool)):
            for y in range(x + 1, len(pool)):
                (la, wa), (lb, wb) = pool[x], pool[y]
                if lb != i or (wa == ends.get(la) and wb == ends.get(lb)):
                    continue  # pairs from the previous line are counted there; the end pair is handled above
                A, B = lines[la][wa], lines[lb][wb]
                if same_stem(A.form, B.form):
                    continue
                t1, t2 = word_tails[(la, wa)], word_tails[(lb, wb)]
                if model.lo_vowel(t1.rhyme[0].nucleus, t2.rhyme[0].nucleus) <= 0:
                    continue  # stressed vowels do not rhyme: quick rejection
                s = model.score(t1, t2)
                if s >= min_internal:
                    out.append(Rhyme("internal", rhyme_type(t1, t2), la, wa, lb, wb, model.length(t1, t2), round(s, 3)))
    return out


def select_rhymes(cands: list[Rhyme], tau_end: float, tau_internal: float) -> list[Rhyme]:
    """End rhymes: the best partner of every line above the threshold; internal: all above the threshold."""
    best: dict[int, Rhyme] = {}
    out = []
    for r in cands:
        if r.kind == "end":
            if r.score >= tau_end and (r.line_b not in best or r.score > best[r.line_b].score):
                best[r.line_b] = r
        elif r.score >= tau_internal:
            out.append(r)
    return list(best.values()) + out
