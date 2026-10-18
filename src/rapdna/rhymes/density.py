"""Rhyme density after Raplyzer (Malmi et al. 2016, „DopeLearning”): for every word, the longest common vowel suffix
with one of the `density_window` previous words; the mean over words. Counts chance vowel matches too, so only
differences between rappers are meaningful, not the value itself."""
from dataclasses import dataclass, field

from rapdna.rhymes.patterns import phonemes, vowels


@dataclass
class Word:
    form: str
    ipa: str
    function: bool = False  # function word (preposition, conjunction, particle, pronoun…)
    vowels: list[str] = field(init=False)

    def __post_init__(self):
        v = vowels()
        self.vowels = [p for p in phonemes(self.ipa) if p in v]


class SectionStream:
    """The vowels of a whole section as one sequence, with the end index of every word."""

    def __init__(self, lines: list[list[Word]]):
        self.vowels: list[str] = []
        self.vowel_word: list[str] = []
        self.word_end: dict[tuple[int, int], int] = {}
        self.order: list[tuple[int, int]] = []
        for li, line in enumerate(lines):
            for wi, w in enumerate(line):
                self.vowels.extend(w.vowels)
                self.vowel_word.extend([w.form.lower()] * len(w.vowels))
                if w.vowels:
                    self.word_end[(li, wi)] = len(self.vowels) - 1
                    self.order.append((li, wi))

    def common_suffix(self, a: tuple[int, int], b: tuple[int, int]) -> int:
        ea, eb = self.word_end[a], self.word_end[b]
        if ea > eb:
            ea, eb = eb, ea
        n = 0
        while (ea - n >= 0 and n < eb - ea and self.vowels[ea - n] == self.vowels[eb - n]
               and (n == 0 or self.vowel_word[ea - n] != self.vowel_word[eb - n])):
            n += 1
        return n


def rhyme_density(lines: list[list[Word]], density_window: int = 15) -> tuple[float, int]:
    """(mean length of the longest vowel match per word, number of words)."""
    stream = SectionStream(lines)
    total = 0
    order = stream.order
    for k, cur in enumerate(order):
        w = lines[cur[0]][cur[1]]
        best = 0
        for prev in order[max(0, k - density_window):k]:
            if lines[prev[0]][prev[1]].form.lower() == w.form.lower():
                continue
            best = max(best, stream.common_suffix(prev, cur))
        total += best
    return (total / len(order) if order else 0.0), len(order)
