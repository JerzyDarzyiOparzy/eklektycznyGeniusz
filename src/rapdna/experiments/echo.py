"""Internal rhymes as echoes of the end rhyme (experiment, not used in the statistics).

1. The **end rhyme** of a line comes from `end.end_match` (shared vowel tail with a line up to WINDOW away).
2. An **echo** is the same vowel pattern (the whole tail or a part of ≥ 2 vowels) inside the neighbouring lines (up to
   2 lines back and forward, also in the same line), starting on a stressed syllable and not overlapping the end rhyme.
Families: lines sharing an end rhyme plus its echoes; every syllable gets a family. Precision was too low for the
statistics (docs/en/internal-rhymes.md).
"""
from dataclasses import dataclass, field

from rapdna.rhymes.end import Verse, end_match, verse_of
from rapdna.rhymes.match import Line
from rapdna.text.nlp import is_function_word

WINDOW = 2


@dataclass
class Rhymes:
    end_len: list[int] = field(default_factory=list)  # end rhyme length of every line (0 = none)
    partner: list[int | None] = field(default_factory=list)
    echoes: list[tuple[int, int, int, int]] = field(default_factory=list)  # (pattern line, echo line, start, length)
    family: dict[tuple[int, int], int] = field(default_factory=dict)  # (line, syllable) → family
    word_pairs: list[tuple[int, int, int, int]] = field(default_factory=list)  # word pairs: (line, syl, line, syl)


def find(lines: list[Line], window: int = WINDOW, min_echo: int = 2, parts: bool = False, words: bool = True) -> Rhymes:
    return find_verse(verse_of(lines), window, min_echo, parts, words,
                      [[is_function_word(f, p) for f, p in zip(line.forms, line.pos)] for line in lines])


def find_verse(V: Verse, window: int = WINDOW, min_echo: int = 2, parts: bool = False, words: bool = False,
               function: list[list[bool]] | None = None) -> Rhymes:
    n = len(V.v)
    R = Rhymes([0] * n, [None] * n)
    for i in range(n):
        for j in range(max(0, i - window), min(n, i + window + 1)):
            if j == i:
                continue
            length = end_match(V, i, j)
            if length > R.end_len[i]:
                R.end_len[i], R.partner[i] = length, j
    parent: dict = {}

    def root(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def unite(a, b):
        parent[root(a)] = root(b)

    # end rhyme families: tail syllables facing each other
    for i in range(n):
        j, length = R.partner[i], R.end_len[i]
        if j is None:
            continue
        for t in range(1, length + 1):
            unite((i, len(V.v[i]) - t), (j, len(V.v[j]) - t))
    # echoes: the tail pattern (or parts of ≥ min_echo vowels) inside the neighbouring lines
    for i in range(n):
        length = R.end_len[i]
        if length < min_echo:
            continue
        pat = V.v[i][len(V.v[i]) - length:]
        pieces = [(0, length)]
        if parts:
            pieces += [(s, e) for s in range(length) for e in range(s + min_echo, length + 1) if (s, e) != (0, length)]
        for j in range(max(0, i - window), min(n, i + window + 1)):
            limit = len(V.v[j]) - R.end_len[j]  # do not overlap the end rhyme of line j
            for s0, e0 in pieces:
                p = pat[s0:e0]
                for s in range(0, limit - len(p) + 1):
                    if not V.stressed[j][s] or V.v[j][s:s + len(p)] != p:
                        continue
                    src = [len(V.v[i]) - length + s0 + t for t in range(len(p))]
                    if V.forms[j][s:s + len(p)] == [V.forms[i][k] for k in src]:
                        continue  # the same words, repetition
                    R.echoes.append((i, j, s, len(p)))
                    for t, k in enumerate(src):
                        unite((j, s + t), (i, k))
    # word pairs: content words with the same vowels from the stress to the word end (≥ 2 vowels or the line end),
    # up to `window` lines apart, different words (dolę / modę / lodzie)
    if words and function is not None:
        keys = []
        for i in range(n):
            spans: dict[int, list[int]] = {}
            for k, w in enumerate(V.word[i]):
                spans.setdefault(w, []).append(k)
            for w, ks in spans.items():
                if function[i][w]:
                    continue
                s0 = next((k for k in ks if V.stressed[i][k]), ks[0])
                tail = [k for k in ks if k >= s0]
                if len(tail) >= 2 or tail[-1] == len(V.v[i]) - 1:
                    keys.append((i, tail, tuple(V.v[i][k] for k in tail), V.forms[i][s0]))
        for x in range(len(keys)):
            for y in range(x + 1, len(keys)):
                (i, ta, ka, fa), (j, tb, kb, fb) = keys[x], keys[y]
                if ka == kb and abs(i - j) <= window and fa != fb:
                    R.word_pairs.append((i, ta[0], j, tb[0]))
                    for a, b in zip(ta, tb):
                        unite((i, a), (j, b))
    ids: dict = {}
    for x in list(parent):
        R.family[x] = ids.setdefault(root(x), len(ids))
    return R


def blocks(R: Rhymes, V: Verse, span: int = 4, col_tol: int = 1) -> tuple[dict, set]:
    """Block rules for families: a family usually holds within
    `span` lines; further only in the same column (the same distance from the line end, ±col_tol syllables); a family
    stays with ≥ 3 occurrences, two are enough in a column; a repeat further than `span` lines outside the column is
    weak. Returns (syllable → new family, set of weak syllables)."""
    occ: dict[int, list[tuple[int, list[int]]]] = {}  # family → occurrences (line, consecutive syllables)
    for (ln, k), f in sorted(R.family.items()):
        lst = occ.setdefault(f, [])
        if lst and lst[-1][0] == ln and lst[-1][1][-1] == k - 1:
            lst[-1][1].append(k)
        else:
            lst.append((ln, [k]))
    out, weak, nid = {}, set(), 0
    for f, items in occ.items():
        from_end = [len(V.v[ln]) - 1 - ks[-1] for ln, ks in items]
        groups: list[list[int]] = []
        for x, (ln, ks) in enumerate(items):
            g = groups[-1] if groups else None
            if g is not None and ln - items[g[0]][0] < span:
                g.append(x)
            elif g is not None and any(abs(from_end[x] - from_end[y]) <= col_tol for y in g):
                g.append(x)  # further than `span` lines, but in the same column
            else:
                groups.append([x])
        for g in groups:
            col = all(abs(from_end[x] - from_end[g[0]]) <= col_tol for x in g)
            if len(g) < 2 or (len(g) == 2 and not col):
                continue
            far = items[g[-1]][0] - items[g[0]][0] >= span
            for x in g:
                ln, ks = items[x]
                for k in ks:
                    out[(ln, k)] = nid
                    if far and not col:
                        weak.add((ln, k))
            nid += 1
    return out, weak
