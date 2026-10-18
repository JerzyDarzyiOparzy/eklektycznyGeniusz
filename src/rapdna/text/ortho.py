"""Split a written word into syllables (for display only): as many parts as the pronunciation has syllables.

A syllable nucleus is a group of vowel letters; „i” before a vowel only softens the consonant („sia-no”, „pia-nka”),
so it belongs to the next vowel's nucleus. Consonants between nuclei: the last one (or a digraph: sz, cz, rz, ch,
dz, dż, dź) goes to the next syllable. When the number of nuclei differs from the pronunciation (often English
words), the whole word is returned.
"""
VOWELS = set("aąeęioóuyAĄEĘIOÓUY")
DIGRAPHS = {"sz", "cz", "rz", "ch", "dz", "dż", "dź"}


def nuclei(word: str) -> list[tuple[int, int]]:
    out, i = [], 0
    while i < len(word):
        if word[i] in VOWELS:
            j = i + 1
            if word[i] in "iI" and j < len(word) and word[j] in VOWELS:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def syllables(word: str, n: int) -> list[str]:
    """The written word cut into n parts (n = syllables in the pronunciation), or [word] when that is not possible."""
    groups = nuclei(word)
    if n <= 1 or len(groups) != n:
        return [word]
    cuts = []
    for (_, e1), (s2, _) in zip(groups, groups[1:]):
        cut = e1 + max(0, s2 - e1 - 1)
        if cut - 1 >= e1 and word[cut - 1:cut + 1].lower() in DIGRAPHS:
            cut -= 1
        cuts.append(cut)
    return [word[a:b] for a, b in zip([0] + cuts, cuts + [len(word)])]
