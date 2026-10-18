# Methodology

## Principles

- **Rules, not models trained on the rappers.** Rhymes are scored by explicit rules and phoneme features. Nothing
  about rhyme is learned from the lyrics being measured, so adding a rapper does not change how the others are
  measured.
- **Validation before comparison.** A feature enters comparisons only after it has been checked against a reference
  (see [validation.md](validation.md)). Weak features are still computed but kept out.
- **Chance control.** Where a feature can arise by chance (rhymes, repetitions), it is compared with the same
  measurement on random lines from different songs.

## From text to sound

1. **Text.** Verses attributed to the rapper, choruses counted once, the Genius footer and ad-libs in brackets
   removed (ad-libs are counted separately).
2. **Word language** (`config/word_language.yaml`). In a Polish line a word is read in English when it is clearly
   more frequent in English („beat”, „trap”, „hype”), unless it is on a list of Polish words and loans („won”, „fury”,
   „bus”). In an English line a word almost unknown in English is read in Polish („jej”, „że”). English stems with
   Polish endings („shotgunem”) are read as hybrids, and neighbouring words in an English phrase follow it („I'll be
   back”, „Frank Castle”). Frequencies come from wordfreq.
3. **Pronunciation (IPA).** In this order: exceptions (`config/pronunciation_exceptions.yaml`), a Polish phonetic
   dictionary built from plWordNet (1.79 million forms), eSpeak NG. English phonemes are mapped to the nearest Polish
   ones, the way a Polish rapper says them. Acronyms that cannot be read as words are spelled out („WKU”), numbers are
   written out.
4. **Syllables and stress.** Syllable boundaries by maximal onset; stress from the dictionary or eSpeak, otherwise
   on the penultimate syllable.
5. **Rhyme units.** A line becomes a sequence of units: a vowel plus the consonants up to the next vowel, across word
   boundaries. „polskie tango” → `[ɔlsk] [ɛt] [aŋɡ] [ɔ]`. The cut falls before the vowel, so the result does not
   depend on where a syllable boundary sits inside a consonant cluster.

## End rhymes

The end rhyme of two lines (up to three lines apart within a verse) is their **longest shared vowel tail that covers
the stress of the last word on both sides** (`rhymes/end.py`). Close vowels count as one (y = i, ę = e, ą = o). The
tail may run across several words, so „polskie tango / grząskie bagno” is a four-syllable rhyme. The same words on
both sides are an epiphora, not a rhyme; a short word hanging at the line end („…moskitierę i”) is skipped.

Each rhyme is described on the axes of the [glossary](glossary.md):

| Axis | Values |
|---|---|
| exactness | exact (consonants of the tail match too) or assonant |
| length | syllables of the shared tail |
| richness | rich when the consonant before the stressed vowel matches („rama / brama”) |
| material | grammatical when both words share a part of speech and an inflectional ending („zrobiłem / kupiłem”), otherwise lexical |

From these come the statistics: mean rhyme length, the share of rhymes with three or more syllables, the share of
rhymed lines, the share of exact rhymes, and the rhyme schemes of consecutive quatrains (AABB, ABAB, monorhyme).

## The rule-based rhyme ruler

For rhymes anywhere in a line, two lines are compared unit by unit along every diagonal of a units × units table
(`rhymes/rules.py`, `rhymes/match.py`).

| Vowels | Score |
|---|---|
| the same | +2 |
| e / ę, o / ą | +1.5 |
| i / y | +1 |
| other | ends the rhyme |

Consonant clusters are aligned for the highest sum: the same consonant +2, different ones
`2 − 8 × (1 − PanPhon similarity)`, an unpaired consonant −1. A rhyme is a run of units whose sum passes a threshold
calibrated on a labelled gold set. The ruler is used for:

- **internal rhymes above chance**: the share of neighbouring line pairs with a rhyme ending inside a line, minus the
  same share in random pairs of the rapper's own lines from different songs (the raw count is mostly chance);
- the chance control of the rhyme schemes;
- `rapdna rhymes-for`: what rhymes with a given word.

## Rhyme density

For every word, the longest vowel sequence shared with one of the 15 previous words, averaged over words (the
Raplyzer method, Malmi et al. 2016). It also counts chance matches, so only differences between rappers are
meaningful.

## Figures

| Figure | Rule |
|---|---|
| Phrase repetition | a run of at least two different words repeats in a line or comes back from the previous line |
| Anaphora / epiphora | neighbouring lines start / end with the same word (not „i / a / bo / że”, no echoes) |
| Alliteration | at least three consecutive content words start with the same sound |
| Similes | „jak”, „niczym”, „jakby”, „niby” followed by a noun, a name or an adjective |
| Wordplay | candidates from fan annotations, homophones, Słowosieć senses and sound vectors; only confirmed ones are shown, as examples |

## Vocabulary and language

| Feature | How |
|---|---|
| Vocabulary | unique lemmas in 8,000 words, mean over 20 random orderings of the songs |
| Lexical variety | MATTR in a moving window of 500 words (100 per song) |
| Word length, syllables per line | from the transcription |
| English words | share of words read in English |
| Rare words | share of Polish words with a wordfreq Zipf below 3 |
| Out-of-dictionary words | Polish forms missing from the dictionary and almost unknown to wordfreq (coinages, slang, loans, typos) |
| Slang | entries of Słownik Miejski that are not in the general dictionary and not frequent in general Polish |
| Vulgarisms | stems from `config/vulgarisms.yaml` |
| Tense and mood | spaCy morphology: past, present, future, imperatives |
| Repetitiveness | compressed / raw size of the rapper's lines in a song |

## Content

| Feature | How |
|---|---|
| Topics | verse fragments of up to four lines embedded with mmlw-roberta-large and clustered with BERTopic; clusters named by hand |
| Perspective | share of 1st person singular, 1st plural, 2nd person and 3rd plural among pronouns and verbs with a person |
| References | proper names (spaCy NER, filtered) and names of other rappers in the corpus, per 1000 words |
| Vocabulary domains | words from hand-written lexicons of sport, war, food, religion and games, per 1000 words |

## Song structure

From Genius section headers and metadata: song length in lines, chorus share, lines per verse, intro and outro,
guests, the rapper's share of a song, producers, ad-libs (bracketed fragments in the raw lyrics), self-mentions and
favourite phrases (word runs in at least three of the rapper's songs that are rare in others).

## Baseline

The Hirjee & Brown model (log-odds of phoneme pairs learned from the corpus, `rhymes/hb.py`) is kept for comparison
only.
