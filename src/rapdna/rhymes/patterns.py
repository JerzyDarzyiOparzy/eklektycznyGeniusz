"""IPA string → phonemes in one inventory (espeak-ng notation mapped to PanPhon notation).

espeak-ng (and the phonetic dictionary) write affricates without a tie bar and use ʃ/ʒ; PanPhon has affricates with a
tie bar and ʂ/ʐ. Phoneme similarity comes from PanPhon features (phonology/features.py).
"""
STRESS = "ˈ"
SECONDARY = "ˌ"
TIE = "͡"
NASAL = "̃"

# order matters (digraphs first)
_ESPEAK_TO_PANPHON = [
    ("tʃ", "t͡ʂ"), ("dʒ", "d͡ʐ"), ("tɕ", "t͡ɕ"), ("dʑ", "d͡ʑ"), ("ts", "t͡s"), ("dz", "d͡z"),
    ("ʃ", "ʂ"), ("ʒ", "ʐ"), ("ç", "x"), ("ɣ", "x"), ("ʲ", ""), ("ː", ""), ("g", "ɡ"),
]

VOWELS = {"a", "ɛ", "i", "ɔ", "u", "ɨ", "ɛ̃", "ɔ̃"}


def normalize_ipa(ipa: str) -> str:
    if TIE in ipa:
        return ipa
    for src, dst in _ESPEAK_TO_PANPHON:
        ipa = ipa.replace(src, dst)
    return ipa


def vowels() -> set[str]:
    return VOWELS


def phonemes(ipa: str) -> list[str]:
    """Split IPA into phonemes: tied affricates and nasal vowels are one element each.
    Stress marks stay separate elements; spaces and other characters are skipped."""
    ipa = normalize_ipa(ipa)
    out: list[str] = []
    i = 0
    while i < len(ipa):
        ch = ipa[i]
        if ch in (STRESS, SECONDARY):
            out.append(ch)
            i += 1
        elif ch.isspace() or ch in "ːˑ.":
            i += 1
        elif i + 2 < len(ipa) and ipa[i + 1] == TIE:
            out.append(ipa[i : i + 3])
            i += 3
        elif i + 1 < len(ipa) and ipa[i + 1] == NASAL:
            out.append(ipa[i : i + 2])
            i += 2
        else:
            out.append(ch)
            i += 1
    return out


def vowel_sequence(ipa: str) -> list[str]:
    return [p for p in phonemes(ipa) if p in VOWELS]


def count_syllables(ipa: str) -> int:
    return len(vowel_sequence(ipa))
