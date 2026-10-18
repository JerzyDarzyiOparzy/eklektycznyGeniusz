"""Methods that were tried for internal rhymes and are not part of the statistics. Each module says what it tried;
results and the reasons for keeping or dropping each method are in docs/en/internal-rhymes.md.

- units, unit_map: syllable units („rhyme blocks”), variants A and B of a learned unit score, and a map to look at;
- vowel_matrix: variant M, assonance chains scored against chance;
- echo: internal rhymes as echoes of the end rhyme;
- families: rhyme families within a verse (used by the local song browser);
- feet: rhymes marked by feet repeated nearby;
- line_pairs: neighbouring lines rhymed position by position (best agreement with the reference annotations);
- probability: a logistic model of „would a listener mark this as a rhyme” on explicit cues.
"""
