"""Rhyme families over a whole verse (as in YouTube rhyme analyses, where the same sounds share one colour). Used by
the local song browser (site/browser.py).

1. For every pair of lines within WINDOW, rhymes come from the rule-based ruler (`match.find` + calibrated thresholds):
   end rhymes and rhymes ending at the end of a content word inside a line. In-word and consonance rhymes are skipped
   (disabled after validation), and so are rhymes on function words („się”, „na”, „jak”), mostly chance.
2. A family is the shared vowel sequence of the rhyme core (from the stress of the last word to the end), with close
   pairs merged (ę → e, ą → o, y → i). „tango / bagno” = family „a-o”, „trend / swęd / cent” = „e”. No chaining
   (A ~ B, B ~ C): chained families merged into one per verse.
3. A family needs at least 2 places in the verse. Letters in order of appearance. Verse scheme = family letter at the
   end of every line („-” when the line end rhymes with nothing), e.g. AABBCC-D.
"""
from dataclasses import dataclass, field
from string import ascii_uppercase

from rapdna.rhymes.match import Line, find, select
from rapdna.text.nlp import is_function_word

WINDOW = 4  # how many lines ahead to look for a rhyme (the whole verse gave many chance matches)
NEAR = {"ɛ̃": "ɛ", "ɔ̃": "ɔ", "ɨ": "i"}


@dataclass
class Span:
    line: int
    k0: int
    k1: int
    key: tuple


@dataclass
class Families:
    spans: list[Span] = field(default_factory=list)
    family: list[int] = field(default_factory=list)
    scheme: str = ""

    def words(self, lines: list[Line]) -> list[dict[int, int]]:
        """For every line: word index → family number (for colouring)."""
        out = [dict() for _ in lines]
        for s, f in zip(self.spans, self.family):
            for k in range(s.k0, s.k1 + 1):
                out[s.line].setdefault(lines[s.line].ks[k].word, f)
        return out


def _key(line: Line, k0: int, k1: int) -> tuple:
    """Vowels of the rhyme core: from the stressed vowel of the last word to the end (close pairs as one)."""
    start = max(k0, line.stress_of_word.get(line.ks[k1].word, k0))
    return tuple(NEAR.get(line.ks[k].v, line.ks[k].v) for k in range(start, k1 + 1))


def families(lines: list[Line], th: dict, window: int = WINDOW, kind: str = "end") -> Families:
    """kind: "end": only rhymes ending at the line end (the verse scheme comes from them), "internal": only rhymes
    inside the line. The layers are separate, each with its own families and letters."""
    found: dict[tuple[int, int], Span] = {}  # (line, last unit) → longest rhyme segment ending there
    for i, a in enumerate(lines):
        for j in range(i, min(len(lines), i + window + 1)):
            b = lines[j]
            if not a.ks or not b.ks or (j > i and a.text_key == b.text_key):
                continue
            for m in select(a, b, find(a, b, same=(i == j)), th):
                if m.anchor != "clausal":
                    continue
                for ln, line, k0, k1 in ((i, a, m.i0, m.i1), (j, b, m.j0, m.j1)):
                    w = line.ks[k1].word
                    if k1 != len(line.ks) - 1 and is_function_word(line.forms[w], line.pos[w]):
                        continue
                    old = found.get((ln, k1))
                    if old is None or k1 - k0 > old.k1 - old.k0:
                        found[(ln, k1)] = Span(ln, k0, k1, _key(line, k0, k1))
    is_end = lambda sp: sp.k1 == len(lines[sp.line].ks) - 1
    spans = sorted((sp for sp in found.values() if is_end(sp) == (kind == "end")), key=lambda s: (s.line, s.k0))
    counts: dict[tuple, int] = {}
    for s in spans:
        counts[s.key] = counts.get(s.key, 0) + 1
    spans = [s for s in spans if counts[s.key] >= 2]
    letter: dict[tuple, int] = {}
    for s in spans:
        letter.setdefault(s.key, len(letter))
    fam = [letter[s.key] for s in spans]
    scheme = []
    for i, ln in enumerate(lines):
        last = len(ln.ks) - 1
        fs = [f for s, f in zip(spans, fam) if s.line == i and s.k1 == last]
        scheme.append(_letter(fs[0]) if fs else "-")
    return Families(spans, fam, "".join(scheme))


def _letter(n: int) -> str:
    return ascii_uppercase[n] if n < 26 else ascii_uppercase[n // 26 - 1] + ascii_uppercase[n % 26]
