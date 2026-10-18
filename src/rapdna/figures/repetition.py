"""Repetition and line-structure figures (plan, phase 3).

Not counted as figures:
- identical or nearly identical lines (a repeat, an echo: „…swoje zgarnąć / Swoje zgarnąć”), i.e. when the shorter
  line is the start/end of the longer one or the lines share ≥ 80% of words;
- interjections and ad-libs at the line boundary („ej”, „yeah”, „ha”);
- anaphora on a bare „i/a/bo/że” or a preposition, unless the first two words agree.

- anaphora / epiphora: neighbouring lines start / end with the same word;
- phrase repetition: a run of ≥ 2 words (at least one content word) occurs twice in the line, or in the line and the
  previous one, outside the start and the end (those are anaphora/epiphora);
- syntactic parallelism: neighbouring lines (≥ 3 words) with a similar sequence of parts of speech.
"""

ANAPHORA_STOP = {"i", "a", "bo", "że", "w", "we", "z", "ze", "na", "o", "u", "do", "to", "się", "ale", "jak"}
INTERJECTIONS = {"ej", "hej", "yeah", "yeh", "ha", "uh", "eh", "yo", "aha", "oh", "ooh", "hmm", "pa", "la", "brr",
                 "skrrt", "huh", "ay", "ayy", "aj", "o", "och", "ach"}


def near_repeat(prev: list[str], cur: list[str]) -> bool:
    short, long_ = sorted((prev, cur), key=len)
    if short == long_[: len(short)] or short == long_[len(long_) - len(short):]:
        return True
    a, b = set(prev), set(cur)
    return len(a & b) / max(1, min(len(a), len(b))) >= 0.8


def is_anaphora(prev: list[str], cur: list[str]) -> bool:
    if not prev or not cur or prev[0] != cur[0] or prev[0] in INTERJECTIONS or near_repeat(prev, cur):
        return False
    if prev[0] not in ANAPHORA_STOP:
        return True
    return len(prev) > 1 and len(cur) > 1 and prev[1] == cur[1]


def is_epiphora(prev: list[str], cur: list[str]) -> bool:
    if not prev or not cur or prev[-1] != cur[-1] or len(cur[-1]) < 2 or cur[-1] in INTERJECTIONS:
        return False
    return not near_repeat(prev, cur)


def count_section(lines: list[list[str]]) -> tuple[int, int]:
    """(anaphoras, epiphoras) in a section; lines are the lower-case words of each line."""
    ana = sum(is_anaphora(lines[i - 1], lines[i]) for i in range(1, len(lines)))
    epi = sum(is_epiphora(lines[i - 1], lines[i]) for i in range(1, len(lines)))
    return ana, epi


def _shared_edges(prev: list[str], cur: list[str]) -> tuple[int, int]:
    """Length of the shared start and the shared end of two lines (in words)."""
    pre = 0
    while pre < min(len(prev), len(cur)) and prev[pre] == cur[pre]:
        pre += 1
    suf = 0
    while suf < min(len(prev), len(cur)) - pre and prev[-1 - suf] == cur[-1 - suf]:
        suf += 1
    return pre, suf


def phrase_repetition_words(prev: list[str], cur: list[str], content: list[bool], n: int = 2) -> set[int]:
    """Indices of the words of the current line that form a repeated phrase (for highlighting in the text).
    A run of n different words (at least one content word) repeated in the line or taken from the previous line.
    A start/end shared with the previous line (anaphora/epiphora) and an echo of the whole line do not count."""
    if prev and near_repeat(prev, cur):
        prev = []
    pre, suf = _shared_edges(prev, cur) if prev else (0, 0)
    grams = [(tuple(cur[i:i + n]), i) for i in range(len(cur) - n + 1)
             if any(content[i:i + n]) and len(set(cur[i:i + n])) == n]
    out: set[int] = set()
    seen_cur: dict[tuple, int] = {}
    for g, i in grams:
        if g in seen_cur and i - seen_cur[g] >= n:
            out |= set(range(seen_cur[g], seen_cur[g] + n)) | set(range(i, i + n))
        seen_cur.setdefault(g, i)
    prev_grams = {tuple(prev[i:i + n]) for i in range(len(prev) - n + 1)}
    for g, i in grams:
        if g in prev_grams and i >= pre and i + n <= len(cur) - suf:
            out |= set(range(i, i + n))
    return out


def has_phrase_repetition(prev: list[str], cur: list[str], content: list[bool], n: int = 2) -> bool:
    return bool(phrase_repetition_words(prev, cur, content, n))


def _pos_distance(a: list[str], b: list[str]) -> float:
    d = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        prev_row, d[0] = d[:], i
        for j in range(1, len(b) + 1):
            d[j] = min(prev_row[j] + 1, d[j - 1] + 1, prev_row[j - 1] + (a[i - 1] != b[j - 1]))
    return d[-1] / max(len(a), len(b), 1)


def is_parallelism(prev_pos: list[str], cur_pos: list[str], prev: list[str], cur: list[str],
                   max_dist: float = 0.4) -> bool:
    """Neighbouring lines (≥ 3 words) with a similar sequence of parts of speech (edit distance ≤ `max_dist`), but
    not the same line and not an echo (the shorter line contained in the longer one)."""
    if min(len(prev_pos), len(cur_pos)) < 3 or abs(len(prev_pos) - len(cur_pos)) > 2 or prev == cur:
        return False
    short, long_ = sorted((prev, cur), key=len)
    if short == long_[:len(short)] or short == long_[len(long_) - len(short):]:
        return False
    return _pos_distance(prev_pos, cur_pos) <= max_dist
