# Internal rhymes

End rhymes are solved (97.8% precision, 96.4% recall). Rhymes inside a line are the open problem: Polish has six
vowels and many identical inflectional endings, so two similar-sounding words occur in almost every pair of lines.
The text alone rarely says which of them the rapper meant.

This page compares the methods that were tried. The code is in `src/rapdna/experiments/`; the comparison runs with
`rapdna compare-rhymes` against the reference rhyme annotations (16 songs, 724 lines, see
[validation.md](validation.md)).

## Measures

Every syllable is either marked or not. Precision is the share of syllables marked by the method that are marked in
the reference, recall the share of reference syllables the method marked. Constants were tuned on half of the songs
and are reported on the other half (test).

## Comparison

| Method | Idea | Syllables P / R / F1 (test) | Kept |
|---|---|---|---|
| Rule-based ruler | sound similarity of word endings anywhere in two lines | at chance level for the raw count | only as a count above chance |
| Shared vowel chains | any chain of vowels shared by neighbouring lines | 2–3 vowels: no excess over chance | no |
| Echo of the end rhyme | the end-rhyme vowel pattern repeated inside nearby lines | about 42% intended | no |
| Syllable matrix | repeated vowel stripes scored by surprise against chance | precision 6–24% | no |
| Learned unit scores | scores for whole rhyme units learned from the corpus | worse than the rules on end rhymes | no |
| Feet | the same vowel key in foot-like cells nearby | 48 / 95 / 63.9 | no: marks twice as much as people |
| Rhyme probability | a logistic model on explicit cues, fitted to the reference | 74 / 82 / 77.7 (leave-one-song-out 75.7 overall) | for comparison |
| **Line pairs** | neighbouring lines rhymed position by position, plus motifs | **79 / 78 / 78.3** | best so far |

## What the reference shows

- 96% of marked fragments rhyme with the line right next to them.
- One rhyme group corresponds to one vowel sequence within a verse in 82–85% of cases: people mark assonance, but
  select it by position, parallelism and runs of syllables.
- The last two syllables of a line are marked in 91–95% of cases; inside a line only 23% of syllables are.
- Choosing internal rhymes from the text alone has a ceiling of about 60% precision, the level reported by
  Hirjee & Brown against hand labels.

## The methods

**Feet.** A line is split into foot-like cells: a stressed syllable with the rest of its word, a short word joined
with the next one, the rest of a longer word. A cell is marked when its vowel key repeats nearby. It finds almost every
rhyme people mark, but marks about twice as much.

**Rhyme probability.** The same cells with explicit features: distance from the line end, a parallel partner in the
next line, an echo of the end rhyme, a run of cells, function words, consonant agreement. A logistic regression
learns only the weights of these cues, from the reference annotations, never from the corpus. The strongest cues:
end rhyme +1.7, being 4 or more syllables away from the end −2.5, function words −0.9, a parallel partner +0.9, a
run of cells +0.7.

**Line pairs.** The reference rhymes neighbouring lines position by position:
„**Chudy** jak Mike **Skinner** **daję** **tłuszcz na** **podkład**” / „**Wczuty** jak w ro**dzinę** **chwalę**
**brud jak** **Bonhart**”. The rule takes the longest run of cells with the same vowel keys in the same order and a
similar place in two neighbouring lines (at least 3 syllables), and adds two-syllable cells whose key is already
marked in the next line (motifs carried through several lines, one word each).

**Recordings.** With aligned recordings, end rhymes land on positions 11–15 of the bar (near the 4th beat, as in the
literature). For internal rhymes the bar position adds little (+0.3 F1), because in these songs a line is about one
bar, so the position in the line carries the same information.

## Whole verses

Instead of single rhymes, a verse can be scored by how densely it is rhymed: the share of marked syllables and the
number of marked syllables per pair of lines. The rank correlation with the reference over 34 sections is 0.5–0.6,
moderate and unstable at this size.

## Next

- More reference annotations, so that the constants can be tuned without reusing the test songs.
- Recordings of the whole corpus, for songs whose lines do not match bars.
- A measured agreement between two people annotating the same verses, the ceiling for any method.
