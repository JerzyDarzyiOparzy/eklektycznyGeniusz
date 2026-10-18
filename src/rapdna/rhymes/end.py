"""End rhymes used in the statistics.

The end rhyme of two lines is their longest common tail of vowels (close pairs count as one: y=i, ę=e, ą=o) that
covers the stress of the last word on both sides; it can run across several words (multi-word rhyme). No consonants
and no tuned thresholds. The same words on both sides (epiphora) are not a rhyme.
Against the reference rhyme annotations: precision 97.8%, recall 96.4% on the last syllable of a line.
"""
from dataclasses import dataclass

import pandas as pd

from rapdna.rhymes.match import Line, is_grammatical

NEAR = {"ɛ̃": "ɛ", "ɔ̃": "ɔ", "ɨ": "i"}


@dataclass
class Verse:
    v: list[list[str]]  # vowels of every line
    stressed: list[list[bool]]
    word: list[list[int]]  # word index of every syllable
    forms: list[list[str]]  # word (lower case) of every syllable
    need: list[int]  # syllables from the stress of the last word to the end of the line


def verse_of(lines: list[Line]) -> Verse:
    V = Verse([], [], [], [], [])
    for line in lines:
        V.v.append([NEAR.get(k.v, k.v) for k in line.ks])
        V.stressed.append([k.stressed for k in line.ks])
        V.word.append([k.word for k in line.ks])
        V.forms.append([line.forms[k.word].lower() for k in line.ks])
        if line.ks:
            last = line.ks[-1].word
            V.need.append(len(line.ks) - line.stress_of_word.get(last, len(line.ks) - 1))
        else:
            V.need.append(0)
    return V


def end_match(V: Verse, i: int, j: int) -> int:
    """Length of the common vowel tail of lines i and j (0 when they do not rhyme)."""
    a, b = V.v[i], V.v[j]
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    if n < max(V.need[i], V.need[j], 1):
        return 0
    if V.forms[i][len(a) - n:] == V.forms[j][len(b) - n:]:
        return 0  # the same words: epiphora
    return n


def end_rhymes(lines_df: pd.DataFrame, words_df: pd.DataFrame, far: int = 3, log=print) -> pd.DataFrame:
    """End rhymes for every pair of lines in a verse up to `far` apart. Same columns as the variant R output
    (kind="end"), so the statistics work unchanged. type: "exact" when all consonants of the tail match too,
    otherwise "assonance"; score = tail length (to pick a line's best partner)."""
    from rapdna.rhymes.ruler_corpus import eligible_lines, lines_by_uid

    eligible = eligible_lines(lines_df)
    built = lines_by_uid(eligible, words_df)
    text = eligible.set_index("line_uid").text.str.lower()
    rows, seen = [], set()
    groups = eligible.sort_values(["song_id", "section", "line"]).groupby(["song_id", "section"], sort=False)
    for n, ((song_id, _), g) in enumerate(groups):
        uids = [u for u in g.line_uid if u in built]
        lines = [built[u] for u in uids]
        V = verse_of(lines)
        for x in range(len(uids)):
            for d in range(1, far + 1):
                y = x + d
                if y >= len(uids) or text[uids[x]] == text[uids[y]]:
                    continue
                key = tuple(sorted((text[uids[x]], text[uids[y]])))
                if key in seen:
                    continue
                seen.add(key)
                length = end_match(V, x, y)
                if not length:
                    continue
                a, b = lines[x], lines[y]
                ka, kb = len(a.ks) - length, len(b.ks) - length
                exact = all(a.ks[ka + t].v == b.ks[kb + t].v and a.ks[ka + t].cons == b.ks[kb + t].cons
                            for t in range(length))
                wa, wb = a.ks[-1].word, b.ks[-1].word
                # rich rhyme: the same consonant before the stressed vowel of the last word (not before the start of
                # the whole tail, which in a multi-word rhyme reaches several words back)
                sa, sb = a.stress_of_word.get(wa, len(a.ks) - 1), b.stress_of_word.get(wb, len(b.ks) - 1)
                rows.append({"song_id": song_id, "artist": g.artist.iloc[0], "line_a": uids[x], "line_b": uids[y],
                             "distance": d, "anchor": "clausal", "kind": "end",
                             "type": "exact" if exact else "assonance", "syllables": length,
                             "score": float(length) - 0.01 * d, "cons_score": float("nan"), "stress_ok": True,
                             "rich": a.ks[sa].pre == b.ks[sb].pre and bool(a.ks[sa].pre),
                             "grammatical": is_grammatical(a.forms[wa], b.forms[wb], a.pos[wa], b.pos[wb], length),
                             "word_a": wa, "word_b": wb, "k_a": [ka, len(a.ks) - 1], "k_b": [kb, len(b.ks) - 1]})
        if n % 2000 == 0:
            log(f"  verses: {n}, end rhymes: {len(rows)}")
    return pd.DataFrame(rows)
