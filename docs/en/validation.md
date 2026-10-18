# Validation

## References

| Reference | Size | Used for |
|---|---|---|
| Gold set | 300 rhyme pairs drawn over the whole score range, 500 random lines | rhyme thresholds, figures |
| Gold set R | 300 candidates of the rule-based ruler, 100 per rhyme kind, over the whole score range | ruler thresholds, rhyme kind |
| Rhyme annotations | 16 songs, 724 lines, 1,988 marked fragments grouped by rhyme, from publicly available rhyme analyses | end rhymes, internal rhymes |
| Samples | 40–100 random hits per feature | references, perspective, similes, English words, vulgarisms |
| Listening checks | recordings of 20 songs | word timing, beats, pronunciation |

The gold sets were labelled blind (the method's score was hidden) by a language model and checked by the author on
samples. Thresholds are chosen on them by cross-validation, so the reported numbers are not fitted to the same data.
The rhyme annotations were made by people and are independent of the project.

## Results

| Feature | Reference | Result | In comparisons |
|---|---|---|---|
| End rhymes | rhyme annotations, last syllable of a line | precision 97.8%, recall 96.4% | yes |
| Rhyme kind (exact / assonant) | gold set R | agreement 86% | yes |
| Internal rhymes, raw count | random lines from other songs | 61% of the count in neighbouring lines | no |
| Internal rhymes above chance | built-in chance control | precision of the rhymes themselves 77% | yes |
| In-word rhymes | gold set R | precision 40% | no |
| Consonance rhymes | gold set R | no true case among 100 candidates | no |
| Anaphora | gold set | precision 89%, recall 67% | computed, out of profiles |
| Epiphora | gold set | precision 92%, recall 92% | computed, out of profiles |
| Phrase repetition | gold set | precision 18/18, recall 86% | yes |
| Alliteration | gold set | precision 5/7 (small sample) | computed, out of profiles |
| Parallelism | gold set | precision 44%, recall 44% | no |
| Enjambment | gold set | recall 1/8 | no |
| Assonance chains | gold set | 0/53 | no |
| Syllables per line | manual count | 24/24 lines | yes |
| English words | sample | precision 40/40 | yes |
| Similes | sample | 34/40 | yes |
| Perspective | sample | 37/40 | yes |
| References | sample | precision 87% | yes |
| Topics | sample | 72% of fragments fit their topic name; 56% of fragments in no topic | with care |

## Chance controls

| Measure | Random / neighbouring lines |
|---|---|
| End rhymes | 0.04–0.13 |
| Internal rhymes (raw) | 0.61 |
| In-word rhymes | 0.64 |
| AABB, ABAB, monorhyme | below 1% of random quatrains |

A feature whose chance level is close to its real level is not used, however plausible its examples look.
