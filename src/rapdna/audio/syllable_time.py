"""Syllable timing from letter alignment (MMS): a syllable starts at the moment of its vowel. The number of vowel
groups in spelling does not always match pronunciation (English words: „Steve” 2 vs 1, „mainstream” 4 vs 2), so:
1) vowel groups from `text.ortho.nuclei`; 2) neighbouring groups are merged („ai”, „ea”); 3) a final „e” after a
consonant is dropped when there are too many groups („Steve”, „wave”); 4) if it still does not match, time is spread
evenly over the word."""
import unicodedata

from rapdna.phonology.syllables import syllabify
from rapdna.text.ortho import nuclei

_PL = str.maketrans("łŁ", "lL")


def _rom_index(word: str, labels: set[str]) -> list[int | None]:
    """Letter index in the word → index in the romanized spelling (None when the letter drops out, e.g. a hyphen)."""
    out, k = [], 0
    for ch in word:
        r = "".join(c for c in unicodedata.normalize("NFKD", ch.translate(_PL).lower()) if c in labels)
        out.append(k if r else None)
        k += len(r)
    return out


def _groups(word: str, n: int) -> list[int] | None:
    """Start letters of n syllable nuclei, or None."""
    g = nuclei(word)
    merged = []
    for a, b in g:
        if merged and a == merged[-1][1]:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    if len(merged) == n:
        return [a for a, _ in merged]
    if len(merged) == n + 1 and word.lower().endswith("e") and merged[-1][0] == len(word) - 1:
        return [a for a, _ in merged[:-1]]
    if len(g) == n:
        return [a for a, _ in g]
    return None


def syllable_onsets(form: str, ipa: str, start: float, end: float, chars: list, labels: set[str]) -> list[float]:
    """Start time of every syllable of the word's pronunciation (IPA)."""
    n = len(syllabify(ipa)) if ipa else 0
    if n == 0:
        return []
    starts = _groups(form, n)
    idx = _rom_index(form, labels)
    if starts is not None and chars:
        out = []
        for a in starts:
            k = next((idx[i] for i in range(a, len(form)) if idx[i] is not None), None)
            if k is None or k >= len(chars):
                break
            out.append(float(chars[k][0]))
        if len(out) == n:
            return out
    return [start + (end - start) * i / n for i in range(n)]
