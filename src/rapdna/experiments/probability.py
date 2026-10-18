"""The probability that a listener takes a cell for a rhyme (experiment; leave-one-song-out F1 75.7 against the
reference annotations, below line_pairs.py at 76.5).

Sound similarity stays rule-based: cells and vowel keys as in `feet.py` (word feet, joins of short words, the end
rhyme from `feet.end_cells`). The model only adds **cue weights** (whether a listener takes a repeat for a rhyme),
fitted to the reference annotations (`validate/train_probability.py`), never to the corpus lyrics:

    p = 1 / (1 + exp(-(intercept + Σ weight · feature)))

Weights and the threshold are explicit in `config/rhyme_probability.yaml`. Features (all 0/1 or small numbers):
- `end`: the cell is an end rhyme (shared vowel tail with a line up to 3 away);
- `from_end_*`: syllables between the cell and the line end (bins);
- `two_syllables`, `stressed`: key length, whether the cell starts on a stressed syllable;
- `function_words`: the cell is made only of function words („na”, „się”, „jak”);
- `kind_*`: the cell kind from `feet.candidates`;
- partner = another cell with the same key up to WINDOW lines away (not the same text): `partners` (log of the
  count), `parallel` (neighbouring line, similar distance from the end), `end_echo` (the key of the end rhyme of this
  or a neighbouring line), `same_line`, `run` (the neighbouring cell also has a partner next to the partner: a
  multi-syllable rhyme), `consonants` (consonant agreement with the best partner, 0–1);
- `line_pair`: the cell belongs to a rhyme run in a pair of neighbouring lines (`line_pairs.py`);
- from a recording (when there is one): `on_beat` (stressed syllable on a beat), `beat_4` (around the 4th beat of
  the bar), `meter_partner` (partner in the same bar position, ±1 sixteenth), `meter_known` (whether timing exists).
"""
import math
from collections import Counter

import yaml

from rapdna import paths
from rapdna.experiments import feet, line_pairs
from rapdna.rhymes.match import Line
from rapdna.text.nlp import is_function_word

CONFIG = paths.CONFIG / "rhyme_probability.yaml"
WINDOW = feet.WINDOW
FE_BINS = [(1, 1), (2, 3), (4, 6), (7, 99)]
COLOR_GAP = line_pairs.COLOR_GAP  # a new colour for the same key after this many lines without it
KINDS = ("foot", "rest", "join", "end_plus_short", "start")


def _fe_name(fe: int) -> str | None:
    for a, b in FE_BINS:
        if a <= fe <= b:
            return f"from_end_{a}_{b}"
    return None


def _cons(c: feet.Cell, lines: list[Line]) -> tuple:
    return tuple(p for k in range(c.start, c.end) for p in lines[c.line].ks[k].cons)


def _cons_sim(a: feet.Cell, b: feet.Cell, lines: list[Line]) -> float:
    A, B = _cons(a, lines), _cons(b, lines)
    if not A and not B:
        return 1.0
    return sum((Counter(A) & Counter(B)).values()) / max(len(A), len(B))


def features(lines: list[Line], meter: list[list[int | None]] | None = None) -> list[tuple[feet.Cell, dict]]:
    """Candidate cells of the verse lines with their features. meter[line][syllable] = bar position 0–15
    (sixteenths) or None."""
    ends, _ = feet.end_cells(lines)
    cands = [c for li, line in enumerate(lines) for c in feet.candidates(li, line)
             if li not in ends or c.end <= ends[li].start] + list(ends.values())
    by_key: dict[tuple, list[feet.Cell]] = {}
    for c in cands:
        by_key.setdefault(c.key, []).append(c)
    by_line: dict[int, list[feet.Cell]] = {}
    for c in cands:
        by_line.setdefault(c.line, []).append(c)
    end_key = {li: c.key for li, c in ends.items()}
    pair_cells = {(c.line, c.start, c.end) for c, _ in line_pairs.mark(lines)}

    def fe(c):
        return len(lines[c.line].ks) - c.end

    def partners(c):
        return [o for o in by_key[c.key] if o is not c and abs(o.line - c.line) <= WINDOW and o.text != c.text
                and (o.line != c.line or o.end <= c.start or c.end <= o.start)]

    part = {c: partners(c) for c in cands}

    def pos(c):
        if meter is None or c.line >= len(meter):
            return None
        k = c.start
        return meter[c.line][k] if k < len(meter[c.line]) else None

    out = []
    for c in cands:
        ps = part[c]
        f = {"end": float(c.kind == "end"), "two_syllables": float(len(c.key) >= 2),
             "stressed": float(lines[c.line].ks[c.start].stressed),
             "function_words": float(all(is_function_word(w) for w in c.text.split())),
             "partners": math.log1p(len(ps)),
             "parallel": float(any(abs(o.line - c.line) == 1 and abs(fe(o) - fe(c)) <= 2 for o in ps)),
             "end_echo": float(c.kind != "end" and any(end_key.get(c.line + d) == c.key for d in (-1, 0, 1))),
             "same_line": float(any(o.line == c.line for o in ps)),
             "consonants": max((_cons_sim(c, o, lines) for o in ps), default=0.0),
             "line_pair": float((c.line, c.start, c.end) in pair_cells)}
        nxt = [o for o in by_line[c.line] if o.start == c.end]
        f["run"] = float(any(any(n2.line == o.line and n2.start == o.end and n2.key == n.key
                                 for n in nxt for n2 in by_line[o.line]) for o in ps))
        for a, b in FE_BINS:
            f[f"from_end_{a}_{b}"] = 0.0
        if c.kind != "end" and (name := _fe_name(fe(c))):
            f[name] = 1.0
        for kind in KINDS:
            f[f"kind_{kind}"] = float(c.kind == kind)
        if meter is not None:
            p = pos(c)
            f["meter_known"] = float(p is not None)
            f["on_beat"] = float(p is not None and p % 4 == 0)
            f["beat_4"] = float(p is not None and 11 <= p <= 13)
            f["meter_partner"] = float(p is not None and any(
                (q := pos(o)) is not None and min(abs(p - q), 16 - abs(p - q)) <= 1 for o in ps))
        out.append((c, f))
    return out


def score(f: dict, w: dict) -> float:
    z = w.get("intercept", 0.0) + sum(w.get(k, 0.0) * v for k, v in f.items())
    return 1 / (1 + math.exp(-z))


def load() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def mark(lines: list[Line], meter: list[list[int | None]] | None = None, cfg: dict | None = None,
         threshold: float | None = None) -> list[tuple[feet.Cell, int, float]]:
    """[(cell, group, probability)]: cells with probability ≥ threshold, no overlaps within a line (higher probability
    wins); a cell without a partner (the same key up to WINDOW lines away, or an end-rhyme pair) is dropped;
    colour = key within the verse. The rule-based end rhyme always goes in; the threshold applies to internal rhymes."""
    cfg = cfg or load()
    audio = meter is not None and "weights_with_audio" in cfg
    w = cfg["weights_with_audio"] if audio else cfg["weights"]
    th = threshold if threshold is not None else (cfg["threshold_with_audio"] if audio else cfg["threshold"])
    scored = sorted(((c, score(f, w)) for c, f in features(lines, meter)), key=lambda x: -x[1])
    taken: dict[int, list[feet.Cell]] = {}
    chosen = []
    for c, p in scored:
        if p < th and c.kind != "end":  # the end rhyme is decided by the rule (feet.end_cells, precision ~97%)
            continue
        if any(not (c.end <= o.start or o.end <= c.start) for o in taken.get(c.line, [])):
            continue
        taken.setdefault(c.line, []).append(c)
        chosen.append((c, p))
    # groups: the same key chained up to WINDOW lines + rule-based end-rhyme pairs (keys may differ in length:
    # „błąd” / „podziurawi rąk”)
    parent = list(range(len(chosen)))

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    order = sorted(range(len(chosen)), key=lambda i: (chosen[i][0].key, chosen[i][0].line, chosen[i][0].start))
    for a, b in zip(order, order[1:]):
        ca, cb = chosen[a][0], chosen[b][0]
        if ca.key == cb.key and cb.line - ca.line <= WINDOW:
            parent[root(a)] = root(b)
    _, links = feet.end_cells(lines)
    end_idx = {c.line: i for i, (c, _) in enumerate(chosen) if c.kind == "end"}
    for i, j in links:
        if i in end_idx and j in end_idx:
            parent[root(end_idx[i])] = root(end_idx[j])
    comps: dict[int, list[int]] = {}
    for i in range(len(chosen)):
        comps.setdefault(root(i), []).append(i)
    # a cell stays when it has a partner (component ≥ 2); group = vowel sequence within the verse, as in the
    # reference annotations (one vowel sequence, one group in 82–85% of cases)
    kept = sorted((i for g in comps.values() if len(g) >= 2 for i in g),
                  key=lambda i: (chosen[i][0].line, chosen[i][0].start))
    colors = line_pairs.color_by_key([chosen[i][0] for i in kept], COLOR_GAP)
    return [(chosen[i][0], col, chosen[i][1]) for i, col in zip(kept, colors)]
