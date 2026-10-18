"""Variant R: rhymes anywhere in two nearby lines (docs/en/methodology.md).

A line becomes one sequence of units across word boundaries. For a pair of lines we scan the diagonals (syllable
against syllable) for segments with a high sum of `rules.py` scores and describe each on the axes of the device
glossary (docs/en/glossary.md).

Anchors: `clausal`: ends at word ends on both sides and covers the stress of those words (end rhymes and most
internal rhymes); `consonance`: same consonants, different vowels; `in_word`: a segment inside words.
"""
import re
from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from rapdna import paths
from rapdna.phonology.syllables import stressed_index, syllabify
from rapdna.rhymes import rules
from rapdna.rhymes.patterns import SECONDARY, STRESS, phonemes

CONFIG = paths.CONFIG / "thresholds_r.yaml"
MIN_INNER = 3  # an in-word rhyme spans at least this many units
FAR_WINDOW = 3  # end rhymes are searched up to 3 lines away; the rest in the same and the neighbouring line


@dataclass
class K:
    """A unit of a line: vowel + consonants up to the next vowel (across word boundaries)."""
    v: str
    cons: tuple = ()
    coda: tuple | None = None  # consonants to the end of the word (last unit of a word only)
    pre: tuple = ()  # consonants right before the vowel
    stressed: bool = False
    word: int = 0
    last: bool = False
    syl: int = 0  # syllable number within the word (for highlighting syllables in text)


@dataclass
class Line:
    ks: list[K]
    forms: list[str]
    lemmas: list[str]
    pos: list[str]
    stress_of_word: dict[int, int] = field(default_factory=dict)  # word → index of its stressed unit

    @property
    def text_key(self) -> str:
        return " ".join(f.lower() for f in self.forms)


def build_line(words: list[tuple[str, str, str, str]]) -> Line:
    """words: (form, ipa, lemma, part of speech) of the words of a line."""
    ks: list[K] = []
    pending: list[str] = []
    stress_of_word: dict[int, int] = {}
    for wi, (form, ipa, _, _) in enumerate(words):
        sylls = syllabify(ipa) if ipa else ()
        if not sylls:  # a word without a vowel („w”, „z”): its consonants join the cluster
            pending += [p for p in phonemes(ipa or "") if p not in (STRESS, SECONDARY)]
            continue
        si = stressed_index(sylls)
        for i, s in enumerate(sylls):
            full = tuple(pending) + s.onset
            if ks:
                ks[-1].cons = full
            ks.append(K(s.nucleus, pre=full, stressed=(i == si), word=wi, last=(i == len(sylls) - 1), syl=i))
            if i == len(sylls) - 1:
                ks[-1].coda = s.coda
            if i == si:
                stress_of_word[wi] = len(ks) - 1
            pending = list(s.coda)
    if ks:
        ks[-1].cons = tuple(pending)
    for k in ks:
        if k.coda is None:
            k.coda = k.cons
    return Line(ks, [w[0] for w in words], [w[2] for w in words], [w[3] for w in words], stress_of_word)


@lru_cache(maxsize=1)
def grammatical_endings() -> list[str]:
    d = yaml.safe_load((paths.CONFIG / "grammatical_endings.yaml").read_text(encoding="utf-8"))
    return sorted({e.lower() for e in d["endings"]}, key=len, reverse=True)


_VOWEL_LETTERS = re.compile(r"[aeiouyąęó]")


def is_grammatical(a: str, b: str, pos_a: str, pos_b: str, syllables: int) -> bool:
    """Grammatical rhyme: same part of speech, a shared ending from the list, and the rhyme does not reach beyond it."""
    a, b = a.lower(), b.lower()
    if pos_a != pos_b:
        return False
    for e in grammatical_endings():
        if a.endswith(e) and b.endswith(e):
            return syllables <= max(1, len(_VOWEL_LETTERS.findall(e)))
    return False


@dataclass
class Match:
    i0: int  # first unit on side A
    i1: int  # last unit on side A
    j0: int
    j1: int
    anchor: str  # clausal | in_word | consonance
    score: float
    cons_score: float = 0.0
    stress_ok: bool = True

    @property
    def syllables(self) -> int:
        return self.i1 - self.i0 + 1


def _cells(a: Line, b: Line, i: int, j: int) -> tuple[float, float]:
    ka, kb = a.ks[i], b.ks[j]
    if a.forms[ka.word].lower() == b.forms[kb.word].lower():
        # the same word facing itself is repetition, not rhyme (docs/en/glossary.md): it breaks the segment
        return rules.OTHER_VOWEL, rules.OTHER_VOWEL
    s_in = rules.unit(ka.v, ka.cons, kb.v, kb.cons)
    s_end = rules.unit(ka.v, ka.coda, kb.v, kb.coda) if ka.last and kb.last else s_in
    return s_in, s_end


def _cons_cells(a: Line, b: Line, i: int, j: int, end: bool) -> float:
    ka, kb = a.ks[i], b.ks[j]
    return rules.cluster(ka.coda, kb.coda) if end else rules.cluster(ka.cons, kb.cons)


def find(a: Line, b: Line, same: bool = False, far: bool = False) -> list[Match]:
    """Rhyme candidates between lines a and b (same: within one line; far: only rhymes at the ends of both lines)."""
    na, nb = len(a.ks), len(b.ks)
    out: list[Match] = []
    if not na or not nb:
        return out
    for off in range(-(na - 1), nb):
        if same and off < 1:
            continue
        i_lo, i_hi = max(0, -off), min(na, nb - off)
        if i_hi - i_lo <= 0:
            continue
        s_in, s_end, pref = [], [], [0.0]
        for i in range(i_lo, i_hi):
            x, y = _cells(a, b, i, i + off)
            s_in.append(x)
            s_end.append(y)
            pref.append(pref[-1] + x)
        run, run_start = 0.0, 0  # Kadane: the best segment ending before the current unit
        for t in range(i_hi - i_lo):
            i, j = i_lo + t, i_lo + t + off
            ka, kb = a.ks[i], b.ks[j]
            start = run_start if run > 0 else t
            # clausal and consonance rhymes: word end on both sides, the stresses of the last words covered
            if (ka.last and kb.last and ka.word in a.stress_of_word and kb.word in b.stress_of_word
                    and (not far or (i == na - 1 and j == nb - 1))):
                ra, rb = a.stress_of_word[ka.word] - i_lo, b.stress_of_word[kb.word] - off - i_lo
                # both stresses in the segment (aligned or shifted), plus the variant that covers the stress on one
                # side only: the rapper stresses another syllable to make the rhyme („mocno / co”), a candidate
                # for shifted stress
                for req in sorted({min(ra, rb), max(ra, rb)}):
                    if not (0 <= req <= t) or (same and i_lo + t >= req + i_lo + off):
                        continue
                    forced = pref[t] - pref[req] + s_end[t]
                    best_ext, ext_start, acc = 0.0, req, 0.0  # extend backwards when it raises the score
                    for u in range(req - 1, -1, -1):
                        acc += s_in[u]
                        if same and i_lo + t >= u + i_lo + off:
                            break
                        if acc > best_ext:
                            best_ext, ext_start = acc, u
                    st = ext_start
                    stress_ok = ra == rb  # both stresses covered and facing each other
                    cons = sum(_cons_cells(a, b, i_lo + u, i_lo + u + off, u == t) for u in range(req, t + 1))
                    out.append(Match(i_lo + st, i, i_lo + st + off, j, "clausal", forced + best_ext, cons, stress_ok))
                    vowels_same = all(a.ks[i_lo + u].v == b.ks[i_lo + u + off].v for u in range(req, t + 1))
                    n_cons = sum(len(a.ks[i_lo + u].coda if u == t else a.ks[i_lo + u].cons) for u in range(req, t + 1))
                    if not vowels_same and n_cons >= 2 and req == min(ra, rb):
                        out.append(Match(i_lo + req, i, i_lo + req + off, j, "consonance", cons, cons, stress_ok))
            # in-word rhyme: any segment of ≥ MIN_INNER units with a pair of stresses facing each other
            if not far and t - start + 1 >= MIN_INNER:
                sc = pref[t] - pref[start] + s_in[t]
                i0 = i_lo + start
                if (not (same and i >= i0 + off) and not (ka.last and kb.last)
                        and any(a.ks[u].stressed and b.ks[u + off].stressed for u in range(i0, i + 1))):
                    out.append(Match(i0, i, i0 + off, j, "in_word", sc, 0.0, True))
            if run > 0:
                run += s_in[t]
            else:
                run, run_start = s_in[t], t
    return out


def tautological(a: Line, b: Line, m: Match) -> bool:
    """The same form or lemma of the last words, or the same text on both sides (repetition, not rhyme)."""
    wa, wb = a.ks[m.i1].word, b.ks[m.j1].word
    if a.forms[wa].lower() == b.forms[wb].lower() or (a.lemmas[wa] and a.lemmas[wa] == b.lemmas[wb]):
        return True
    span_a = [a.forms[w].lower() for w in sorted({a.ks[u].word for u in range(m.i0, m.i1 + 1)})]
    span_b = [b.forms[w].lower() for w in sorted({b.ks[u].word for u in range(m.j0, m.j1 + 1)})]
    return span_a == span_b


def select(a: Line, b: Line, cands: list[Match], thresholds: dict) -> list[Match]:
    """Candidates above the thresholds, without tautologies or overlaps (highest scores first)."""
    keep: list[Match] = []
    for m in sorted(cands, key=lambda m: -m.score):
        key = m.anchor
        if key == "clausal" and m.i1 == len(a.ks) - 1 and m.j1 == len(b.ks) - 1:
            key = "clausal_end"  # end rhyme: threshold from the gold set of line-end pairs (198 pairs)
        if m.score < thresholds.get(key, thresholds[m.anchor]) or tautological(a, b, m):
            continue
        if any(not (m.i1 < k.i0 or m.i0 > k.i1) or not (m.j1 < k.j0 or m.j0 > k.j1) for k in keep):
            continue
        keep.append(m)
    return keep


def describe(a: Line, b: Line, m: Match) -> dict:
    """Dictionary axes of one rhyme (docs/en/methodology.md)."""
    # exactness over the whole repeated sequence (docs/en/glossary.md); judging only the core (from the
    # stress of the last word) agreed worse with judging by ear (0.83 vs 0.86), e.g. „ale czuję / razie czuj się”
    i0, j0, n = m.i0, m.j0, m.syllables
    rng = range(n)
    va = [a.ks[i0 + u].v for u in rng]
    vb = [b.ks[j0 + u].v for u in rng]
    ca = [a.ks[i0 + u].coda if u == n - 1 and m.anchor != "in_word" else a.ks[i0 + u].cons for u in rng]
    cb = [b.ks[j0 + u].coda if u == n - 1 and m.anchor != "in_word" else b.ks[j0 + u].cons for u in rng]
    if va == vb:
        typ = "exact" if ca == cb else "assonance"
    else:
        typ = "consonance" if ca == cb and any(ca) else "approx"
    pa, pb = a.ks[m.i0].pre, b.ks[m.j0].pre
    wa, wb = a.ks[m.i1].word, b.ks[m.j1].word
    end = m.i1 == len(a.ks) - 1 and m.j1 == len(b.ks) - 1 and m.anchor != "in_word"
    return {
        "anchor": m.anchor, "kind": "end" if end else "internal", "type": typ, "syllables": m.syllables,
        "score": round(m.score, 3), "cons_score": round(m.cons_score, 3), "stress_ok": bool(m.stress_ok),
        "rich": bool(pa and pb and pa[-1] == pb[-1]),
        "grammatical": m.anchor != "in_word" and is_grammatical(a.forms[wa], b.forms[wb], a.pos[wa], b.pos[wb],
                                                                m.syllables),
        "word_a": wa, "word_b": wb, "k_a": [m.i0, m.i1], "k_b": [m.j0, m.j1],
    }


def pair_score(a: Line, wa: int, b: Line, wb: int) -> float:
    """Clausal score for a given pair of words (for comparison on the first gold set)."""
    ia = [i for i, k in enumerate(a.ks) if k.word == wa]
    jb = [j for j, k in enumerate(b.ks) if k.word == wb]
    if not ia or not jb:
        return -99.0
    i, j = ia[-1], jb[-1]
    best = [m.score for m in find(a, b) if m.anchor == "clausal" and m.i1 == i and m.j1 == j]
    return max(best) if best else -99.0


def thresholds() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
