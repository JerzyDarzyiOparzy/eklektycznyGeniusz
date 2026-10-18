"""Experiment, variant M: rhymes as repeated vowel sequences in the syllable matrix of a verse
(docs/en/internal-rhymes.md). Rejected: precision 6–24% against the reference annotations.

A verse is one sequence of syllables. A rhyme is a diagonal stripe in the „same vowel” matrix (assonance), scored by
surprise: the information of the matched vowels minus log2 of the number of places where it could occur by chance.
A rhyme when the score ≥ 0. Families are the connected components of the network of syllables joined by stripes.
"""
import json
import math
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from rapdna import paths
from rapdna.rhymes.match import Line
from rapdna.rhymes.patterns import vowel_sequence

NEAR = {"ɛ̃": "ɛ", "ɔ̃": "ɔ", "ɨ": "i"}  # close pairs as in the definition of rhyme (ę/e, ą/o, y/i)
WINDOW = 4  # lines: the same one and up to 4 further, like the family window of variant R
COLUMN_TOL = 1  # „column”: the same distance from the end or the start of the line, ±1 syllable
VOWEL_FREQ = paths.RESOURCES / "vowel_freq_pl.json"


@lru_cache(maxsize=1)
def vowel_probs() -> dict[str, float]:
    """Vowel frequencies of general Polish: the 50k most frequent words (wordfreq) from the phonetic dictionary,
    weighted by word frequency. Not from the rappers' lyrics (a rhyme measure is never learned on what it measures)."""
    if VOWEL_FREQ.exists():
        return json.loads(VOWEL_FREQ.read_text(encoding="utf-8"))
    from wordfreq import top_n_list, word_frequency

    words = top_n_list("pl", 50000)
    d = pd.read_parquet(paths.PHONETIC_DICT, filters=[("word", "in", words)]).drop_duplicates("word")
    counts: dict[str, float] = {}
    for w, ipa in zip(d.word, d.ipa):
        f = word_frequency(w, "pl")
        for v in vowel_sequence(ipa):
            v = NEAR.get(v, v)
            counts[v] = counts.get(v, 0.0) + f
    total = sum(counts.values())
    probs = {v: c / total for v, c in sorted(counts.items())}
    VOWEL_FREQ.write_text(json.dumps(probs, ensure_ascii=False, indent=1), encoding="utf-8")
    return probs


def info(vowels) -> float:
    """Information (bits) of matching these vowels: −log2 of the probability that random syllables repeat them."""
    p = vowel_probs()
    return sum(-math.log2(p.get(v, min(p.values()))) for v in vowels)


@dataclass
class Syl:
    v: str
    stressed: bool
    line: int
    word: int
    pos: int  # syllable number in the line
    from_end: int  # syllables left to the end of the line


@dataclass
class Run:
    i: int  # first syllable of side A (index in the verse sequence)
    j: int  # first syllable of side B
    n: int  # stripe length
    column: bool
    score: float  # bits above chance


def syllables(lines: list[Line]) -> list[Syl]:
    out = []
    for li, line in enumerate(lines):
        n = len(line.ks)
        for p, k in enumerate(line.ks):
            out.append(Syl(NEAR.get(k.v, k.v), k.stressed, li, k.word, p, n - 1 - p))
    return out


def _is_column(a0: Syl, a1: Syl, b0: Syl, b1: Syl) -> bool:
    return a0.line != b0.line and (abs(a1.from_end - b1.from_end) <= COLUMN_TOL or abs(a0.pos - b0.pos) <= COLUMN_TOL)


def _repeat(lines: list[Line], sy: list[Syl], r: tuple[int, int, int]) -> bool:
    """Repetition instead of rhyme: the same text on both sides or one word with the same lemma."""
    i, j, n = r
    wa = sorted({(sy[i + t].line, sy[i + t].word) for t in range(n)})
    wb = sorted({(sy[j + t].line, sy[j + t].word) for t in range(n)})
    fa = [lines[l].forms[w].lower() for l, w in wa]
    fb = [lines[l].forms[w].lower() for l, w in wb]
    if fa == fb:
        return True
    if len(wa) == 1 and len(wb) == 1:
        (la, a), (lb, b) = wa[0], wb[0]
        return lines[la].lemmas[a] == lines[lb].lemmas[b]
    return False


def _places(sy: list[Syl], i: int, j: int, L: int, col: bool, cand_lines: int, cand_syl: list[int]) -> float:
    """How many times such a match could have occurred by chance Counted for every start syllable of the line (counting
    places for a single start syllable gave about 190 chance „rhymes” per verse). For a match at the end of both lines: one place per line (as many as lines in the window);
    in another column: lines × (2·COLUMN_TOL + 1) positions × 2 (from the start or the end) × syllables of the line;
    anywhere else: syllables in the window × syllables of the line."""
    a1, b1 = sy[i + L - 1], sy[j + L - 1]
    if a1.from_end == 0 and b1.from_end == 0 and a1.line != b1.line:
        return max(1, cand_lines)
    per_line = sy[i].pos + sy[i].from_end + 1
    if col:
        return max(1, cand_lines) * (2 * COLUMN_TOL + 1) * 2 * per_line
    return max(1, len(cand_syl)) * per_line


def find_runs(lines: list[Line], window: int = WINDOW) -> tuple[list[Syl], list[Run]]:
    sy = syllables(lines)
    n = len(sy)
    first_of_line = {}
    for k, s in enumerate(sy):
        first_of_line.setdefault(s.line, k)
    runs = []
    for i in range(n):
        last_line = sy[i].line + window
        cand_syl = [j for j in range(i + 1, n) if sy[j].line <= last_line]
        cand_lines = len({sy[j].line for j in cand_syl if sy[j].line != sy[i].line})
        for j in cand_syl:
            if sy[i].v != sy[j].v:
                continue
            if i > 0 and sy[i - 1].v == sy[j - 1].v and j - 1 > i - 1 and sy[j - 1].line <= sy[i - 1].line + window:
                continue  # the stripe extends backwards: count it from its start
            L = 1
            while i + L < j and j + L < n and sy[i + L].v == sy[j + L].v:
                L += 1
            if not any(sy[i + t].stressed for t in range(L)) or not any(sy[j + t].stressed for t in range(L)):
                continue
            if _repeat(lines, sy, (i, j, L)):
                continue
            col = _is_column(sy[i], sy[i + L - 1], sy[j], sy[j + L - 1])
            score = info(sy[i + t].v for t in range(L)) - math.log2(_places(sy, i, j, L, col, cand_lines, cand_syl))
            runs.append(Run(i, j, L, col, score))
    return sy, runs


def families(lines: list[Line], window: int = WINDOW) -> tuple[list[Syl], list[Run], dict[int, int]]:
    """Rhymes (stripes with score ≥ 0) and families: syllable → connected component of the syllable network."""
    sy, runs = find_runs(lines, window)
    rhymes = [r for r in runs if r.score >= 0]
    parent = list(range(len(sy)))

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in rhymes:
        for t in range(r.n):
            parent[root(r.i + t)] = root(r.j + t)
    linked = {r.i + t for r in rhymes for t in range(r.n)} | {r.j + t for r in rhymes for t in range(r.n)}
    ids: dict[int, int] = {}
    fam = {}
    for k in sorted(linked):
        fam[k] = ids.setdefault(root(k), len(ids))
    return sy, rhymes, fam


def end_score(a: Line, wa: int, b: Line, wb: int) -> float:
    """A pair of ends (word wa in a, wb in b): a stripe from the end of both words backwards, covering the stress of
    the last word on both sides; like a column at the line end (4 possible places in the window → 2 bits). No rhyme:
    −10."""
    ka = [k for k in range(len(a.ks)) if a.ks[k].word <= wa]
    kb = [k for k in range(len(b.ks)) if b.ks[k].word <= wb]
    if not ka or not kb:
        return -10.0
    va = [NEAR.get(a.ks[k].v, a.ks[k].v) for k in ka]
    vb = [NEAR.get(b.ks[k].v, b.ks[k].v) for k in kb]
    L = 0
    while L < min(len(va), len(vb)) and va[-1 - L] == vb[-1 - L]:
        L += 1
    need_a = ka[-1] - a.stress_of_word.get(wa, ka[-1]) + 1
    need_b = kb[-1] - b.stress_of_word.get(wb, kb[-1]) + 1
    if L < max(need_a, need_b):
        return -10.0
    return info(va[len(va) - L:]) - math.log2(WINDOW)
