"""Rhymes in pairs of neighbouring lines (experiment; the best agreement with the reference annotations, F1 78.3 on
held-out songs).

In the reference annotations 96% of marked fragments rhyme with the line right next to them, and one group
corresponds to one vowel sequence within a verse (82–85%). So a rhyme is **a pair of neighbouring lines rhymed
position by position**: „**Chudy** jak Mike **Skinner** **daję** **tłuszcz na** **podkład**” / „**Wczuty** jak
w ro**dzinę** **chwalę** **brud jak** **Bonhart**” (u-y / i-e / a-e / u-a / o-a). In line with the literature,
rhymed syllables sit in the same rhythmic place (Maler & Komaniecki 2021).

Rule:
1. The end rhyme from `feet.end_cells` (shared vowel tail), always.
2. Every line is split into cells from `feet.candidates`: word foot, one-syllable word + the whole next word
   („tłuszcz na”), the rest of the word before the foot („kosz|marem”). Cells made only of function words are skipped.
3. For every pair of neighbouring lines, find the longest run of cell pairs with the same vowel key (y=i, ę=e, ą=o), in
   the same order in both lines and in a similar place (distance from the line end differs by ≤ TOL syllables). The run
   counts when it covers ≥ MIN_SYL syllables on each side; then all its cells are marked. A single echo is not.
4. Motif: a two-syllable cell is marked when the same key is already marked (by steps 1–3) in the neighbouring line;
   one vowel pattern is often carried through several lines, one word each.
5. Group = vowel key within the verse; a new group for the same key only after a gap > COLOR_GAP lines.
Constants were tuned on half of the songs and checked on the other half.
"""
from rapdna.experiments import feet
from rapdna.rhymes.match import Line
from rapdna.text.nlp import is_function_word

KINDS = {"foot", "join", "rest"}
TOL = 2
MIN_SYL = 3
COLOR_GAP = 8  # tuned on the development songs (pair measure within a group)


def _function(c: feet.Cell) -> bool:
    return all(is_function_word(w) for w in c.text.split())


def _cuts_word(c: feet.Cell, line: Line) -> bool:
    """A join that takes only the start of the next word („styl pa|kuję”); people join a short word with the whole
    next one („Kix beats”, „tłuszcz na”, „idź stąd”)."""
    return c.kind == "join" and c.end < len(line.ks) and line.ks[c.end].word == line.ks[c.end - 1].word


def cells(li: int, line: Line, ends: dict[int, feet.Cell]) -> list[feet.Cell]:
    end = ends.get(li)
    cs = [c for c in feet.candidates(li, line) if c.kind in KINDS and not _function(c)
          and (end is None or c.end <= end.start) and not _cuts_word(c, line)]
    if end is not None:
        cs.append(end)
    return sorted(cs, key=lambda c: (c.start, c.end))


def chain(A: list[feet.Cell], B: list[feet.Cell], la: Line, lb: Line) -> tuple[int, list[tuple]]:
    """The longest (in syllables) run of cell pairs with equal keys, increasing in both lines."""
    def fe(c, line):
        return len(line.ks) - c.end

    best: dict[tuple[int, int], tuple[int, list]] = {}
    for i, a in enumerate(A):
        for j, b in enumerate(B):
            if a.key != b.key or a.text == b.text or abs(fe(a, la) - fe(b, lb)) > TOL:
                continue
            prev = max((v for (i2, j2), v in best.items() if A[i2].end <= a.start and B[j2].end <= b.start),
                       key=lambda v: v[0], default=(0, []))
            best[(i, j)] = (prev[0] + len(a.key), prev[1] + [(a, b)])
    return max(best.values(), key=lambda v: v[0], default=(0, []))


def mark(lines: list[Line]) -> list[tuple[feet.Cell, int]]:
    """[(cell, colour)]: colour = number of the vowel key within the verse."""
    ends, links = feet.end_cells(lines)
    C = [cells(li, line, ends) for li, line in enumerate(lines)]
    chosen: dict[tuple[int, int, int], feet.Cell] = {}
    for li in range(len(lines) - 1):
        score, pairs = chain(C[li], C[li + 1], lines[li], lines[li + 1])
        if score >= MIN_SYL:
            for a, b in pairs:
                chosen[(a.line, a.start, a.end)] = a
                chosen[(b.line, b.start, b.end)] = b
    for i, j in links:
        for x in (i, j):
            chosen[(x, ends[x].start, ends[x].end)] = ends[x]
    # cells from two pairs (with the line above and below) may overlap: the longer one stays
    out, taken = [], {}
    for c in sorted(chosen.values(), key=lambda c: -(c.end - c.start)):
        if any(not (c.end <= o.start or o.end <= c.start) for o in taken.get(c.line, [])):
            continue
        taken.setdefault(c.line, []).append(c)
        out.append(c)
    # motif: a two-syllable cell whose key is already coloured in the neighbouring line („ode mnie / wszędzie /
    # czerpie / siebie / jeden”: one vowel sequence through several lines, one word each); one round, only from
    # cells of steps 1–3
    base = list(out)
    for li, line in enumerate(lines):
        for c in sorted((c for c in C[li] if c.kind != "end" and len(c.key) >= 2), key=lambda c: -(c.end - c.start)):
            if any(not (c.end <= o.start or o.end <= c.start) for o in taken.get(li, [])):
                continue
            if any(o.key == c.key and abs(o.line - li) == 1 for o in base):
                taken.setdefault(li, []).append(c)
                out.append(c)
    out.sort(key=lambda c: (c.line, c.start))
    return list(zip(out, color_by_key(out)))


def color_by_key(cs: list[feet.Cell], gap: int = COLOR_GAP) -> list[int]:
    """Colour of every cell (in line order): the same key → the same colour, a new one after a gap > gap lines."""
    last: dict[tuple, tuple[int, int]] = {}  # key → (last line, colour)
    out, n = [], 0
    for c in cs:
        if c.key not in last or c.line - last[c.key][0] > gap:
            last[c.key], n = (c.line, n), n + 1
        last[c.key] = (c.line, last[c.key][1])
        out.append(last[c.key][1])
    return out
