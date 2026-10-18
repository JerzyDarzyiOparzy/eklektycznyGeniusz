"""Marking rhymes by feet (experiment). A line is split into foot-like cells; a cell is marked when the same vowel
sequence repeats nearby.

Cell candidates (syllable indices of the line = units from `match.build_line`):
- **foot**: the stressed syllable of a word + the rest of the word („skroni”, „karę”, „Glock”);
- **rest** of the word before the foot, cut from the end into pieces of 2 syllables („kosz|marem” → „kosz”);
- **join**: a one-syllable word + the first syllable of the next word („to przy”, „Jak Bi”, „ten team”);
- **end_plus_short**: the last syllable of a word + a one-syllable word („satysfak-cję przy”);
- **start**: the first two syllables of a longer word („Robi-my”, „Aven-gers”), lowest priority;
- **end**: the end rhyme of the line (rule from `rhymes/end.py`), fixed first.
Choice: a cell is marked only when its key (vowels, y=i, ę=e, ą=o) repeats in another cell up to WINDOW lines away
(also in the same line; not the same word, not the same text); cells of a line do not overlap; longer keys first,
then word feet, then more repeats. Groups: cells with the same key chained (each up to WINDOW lines from the previous
one); a group stays with ≥ 3 cells or 2 in neighbouring lines; a group of two one-syllable cells only when they stand
in parallel (neighbouring lines, similar distance from the line end).
Against the reference annotations: recall about 95%, precision 47%; it marks about twice as much as people do.
"""
from dataclasses import dataclass, replace

from rapdna.rhymes.end import end_match, verse_of
from rapdna.rhymes.match import Line

NEAR = {"ɛ̃": "ɛ", "ɔ̃": "ɔ", "ɨ": "i"}
WINDOW = 4
END_FAR = 3  # end rhymes: up to 3 lines away, as in the statistics (rhymes/end.py)
PRIORITY = {"end": 4, "foot": 3, "rest": 2, "join": 2, "end_plus_short": 2, "start": 1}
# short words hanging at the line end before an enjambment or as an exclamation („…moskitierę i”, „…obwarzanka, yo”):
# the end rhyme is taken on the word before them
TRAILING = {"i", "a", "bo", "że", "yo", "jo", "aj", "ej", "oj", "no", "ha", "uh", "yeah", "ye"}


@dataclass(frozen=True)
class Cell:
    line: int
    start: int  # first syllable (unit) in the line
    end: int  # one past the last
    key: tuple
    kind: str
    text: str  # words of the cell (to exclude repeats)


def _key(line: Line, ks: list[int]) -> tuple:
    return tuple(NEAR.get(line.ks[k].v, line.ks[k].v) for k in ks)


def candidates(li: int, line: Line) -> list[Cell]:
    words: dict[int, list[int]] = {}
    for k, kl in enumerate(line.ks):
        words.setdefault(kl.word, []).append(k)
    order = list(words.items())
    out = []

    def add(ks, kind):
        if ks:
            ws = sorted({line.ks[k].word for k in ks})
            out.append(Cell(li, ks[0], ks[-1] + 1, _key(line, ks), kind, " ".join(line.forms[w].lower() for w in ws)))

    for wi, (w, ks) in enumerate(order):
        si = next((k for k in ks if line.ks[k].stressed), ks[-2] if len(ks) >= 2 else ks[-1])
        add(ks[ks.index(si):], "foot")
        rest = ks[:ks.index(si)]
        while rest:
            chunk = rest[-2:]
            add(chunk, "rest")
            rest = rest[:-len(chunk)]
        if len(ks) >= 3:
            add(ks[:2], "start")
        if len(ks) == 1 and wi + 1 < len(order):
            add([ks[0], order[wi + 1][1][0]], "join")
        if len(ks) == 1 and wi > 0 and len(order[wi - 1][1]) >= 2:
            add([order[wi - 1][1][-1], ks[0]], "end_plus_short")
    return out


def _parallel(a: Cell, b: Cell, lines: list[Line], tol: int = 2) -> bool:
    fa, fb = len(lines[a.line].ks) - a.end, len(lines[b.line].ks) - b.end
    return abs(a.line - b.line) == 1 and abs(fa - fb) <= tol


def _from_end(c: Cell, lines: list[Line]) -> int:
    return len(lines[c.line].ks) - c.end


def _strong(a: Cell, b: Cell, lines: list[Line], run: bool) -> bool:
    """Strong link (point 4 of the scheme): part of a repeated run of cells (multi-syllable rhyme), the same line,
    both line ends, or lines up to 2 apart in a similar place. One-syllable cells only in a run, at the ends of
    neighbouring lines or in parallel in the neighbouring line."""
    d, fa, fb = abs(a.line - b.line), _from_end(a, lines), _from_end(b, lines)
    if run:
        return True
    if len(a.key) == 1:
        return (fa == 0 and fb == 0 and d <= 2) or (d == 1 and abs(fa - fb) <= 1)
    return d == 0 or (fa == 0 and fb == 0) or (d <= 2 and abs(fa - fb) <= 3)


def mark(lines: list[Line], window: int = WINDOW, strict: bool = True) -> list[tuple[Cell, int]]:
    """[(cell, group number)]: coloured cells. strict=False: the first version (without point 4 of the scheme)."""
    if strict:
        return _mark_strict(lines, window)
    cands = [c for li, line in enumerate(lines) for c in candidates(li, line)]
    partners: dict[Cell, set[Cell]] = {c: set() for c in cands}
    by_key: dict[tuple, list[Cell]] = {}
    for c in cands:
        by_key.setdefault(c.key, []).append(c)
    for cs in by_key.values():
        for x in range(len(cs)):
            for y in range(x + 1, len(cs)):
                a, b = cs[x], cs[y]
                if abs(a.line - b.line) > window or a.text == b.text:
                    continue
                if a.line == b.line and not (a.end <= b.start or b.end <= a.start):
                    continue
                partners[a].add(b)
                partners[b].add(a)
    order = sorted((c for c in cands if partners[c]),
                   key=lambda c: (-len(c.key), -PRIORITY[c.kind], -len(partners[c]), c.line, c.start))
    taken: dict[int, list[Cell]] = {}
    chosen: list[Cell] = []
    for c in order:
        if any(not (c.end <= o.start or o.end <= c.start) for o in taken.get(c.line, [])):
            continue
        taken.setdefault(c.line, []).append(c)
        chosen.append(c)
    chosen_set = set(chosen)
    chosen = [c for c in chosen if partners[c] & chosen_set]  # the partner may have lost to another cell
    groups: list[list[Cell]] = []  # the same key, chained up to `window` lines
    for key in sorted({c.key for c in chosen}):
        cs = sorted((c for c in chosen if c.key == key), key=lambda c: (c.line, c.start))
        cur = [cs[0]]
        for c in cs[1:]:
            if c.line - cur[-1].line <= window:
                cur.append(c)
            else:
                groups.append(cur)
                cur = [c]
        groups.append(cur)
    out, gid = [], 0
    for g in groups:
        if len(g) < 2:
            continue
        if len(g) == 2 and abs(g[0].line - g[1].line) > 1:
            continue
        if len(g[0].key) == 1 and len(g) == 2 and not _parallel(g[0], g[1], lines):
            continue
        out += [(c, gid) for c in g]
        gid += 1
    return out


def _trim(line: Line) -> Line:
    """Drop a one-syllable word from TRAILING at the line end, when another word comes before it."""
    ks = list(line.ks)
    while (len({k.word for k in ks}) > 1 and line.forms[ks[-1].word].lower() in TRAILING
           and sum(k.word == ks[-1].word for k in ks) == 1):
        ks.pop()
    return replace(line, ks=ks) if len(ks) < len(line.ks) else line


def end_cells(lines: list[Line], far: int = END_FAR) -> tuple[dict[int, Cell], list[tuple[int, int]]]:
    """End rhymes: a line has one when it shares a vowel tail covering the stress of the last word with a line up to
    `far` away (`end.end_match`). Cell = from the stress of the last word to the line end."""
    trimmed = [_trim(line) for line in lines]
    V = verse_of(trimmed)
    links = [(i, j) for i in range(len(lines)) for j in range(i + 1, min(len(lines), i + far + 1))
             if trimmed[i].ks and trimmed[j].ks and end_match(V, i, j)]
    cells = {}
    for i in sorted({x for p in links for x in p}):
        n = len(trimmed[i].ks)
        ks = list(range(n - max(V.need[i], 1), n))
        words = sorted({lines[i].ks[k].word for k in ks})
        cells[i] = Cell(i, ks[0], n, _key(lines[i], ks), "end", " ".join(lines[i].forms[w].lower() for w in words))
    return cells, links


def _mark_strict(lines: list[Line], window: int) -> list[tuple[Cell, int]]:
    ends, end_links = end_cells(lines)
    # the end rhyme is fixed first: other cells cannot take its syllables („na błąd” instead of „błąd”)
    cands = [c for li, line in enumerate(lines) for c in candidates(li, line)
             if li not in ends or c.end <= ends[li].start] + list(ends.values())
    by_line: dict[int, list[Cell]] = {}
    for c in cands:
        by_line.setdefault(c.line, []).append(c)
    nxt = {c: [o for o in by_line[c.line] if o.start == c.end] for c in cands}
    prv = {c: [o for o in by_line[c.line] if o.end == c.start] for c in cands}
    by_key: dict[tuple, list[Cell]] = {}
    for c in cands:
        by_key.setdefault(c.key, []).append(c)
    same = {}
    for cs in by_key.values():
        for x in range(len(cs)):
            for y in range(x + 1, len(cs)):
                a, b = cs[x], cs[y]
                if abs(a.line - b.line) > window or a.text == b.text:
                    continue
                if a.line == b.line and not (a.end <= b.start or b.end <= a.start):
                    continue
                same[(a, b)] = same[(b, a)] = True

    def in_run(a, b):
        """The neighbouring cell of a and the neighbouring cell of b (on the same side) share a key too."""
        return (any((x, y) in same for x in nxt[a] for y in nxt[b])
                or any((x, y) in same for x in prv[a] for y in prv[b]))

    strong: dict[Cell, set[Cell]] = {c: set() for c in cands}
    for (a, b) in same:
        if _strong(a, b, lines, in_run(a, b)):
            strong[a].add(b)
    order = list(ends.values()) + sorted((c for c in cands if strong[c] and c.kind != "end"),
                                         key=lambda c: (-len(c.key), -PRIORITY[c.kind], -len(strong[c]), c.line, c.start))
    taken: dict[int, list[Cell]] = {}
    chosen = []
    for c in order:
        if any(not (c.end <= o.start or o.end <= c.start) for o in taken.get(c.line, [])):
            continue
        taken.setdefault(c.line, []).append(c)
        chosen.append(c)
    chosen_set = set(chosen)
    parent = {c: c for c in chosen}

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for c in chosen:
        for o in strong[c] & chosen_set:
            parent[root(c)] = root(o)
    for i, j in end_links:
        parent[root(ends[i])] = root(ends[j])
    comps: dict[Cell, list[Cell]] = {}
    for c in chosen:
        comps.setdefault(root(c), []).append(c)
    out, gid = [], 0
    for cs in sorted(comps.values(), key=lambda g: (min(c.line for c in g), min(c.start for c in g))):
        if len(cs) < 2:
            continue
        out += [(c, gid) for c in cs]
        gid += 1
    return out
