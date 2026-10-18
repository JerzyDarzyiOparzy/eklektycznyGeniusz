# Features

Everything that can describe a rapper's style, grouped into eight dimensions, with its status.

**Status:** **in use**: validated and used in comparisons and profiles; **computed**: computed, kept out of
comparisons until validated; **planned**: the data or method exists, not yet computed; **hard**: possible, with
uncertain quality or nothing to check against; **off**: checked and too weak.

**Balance.** In rapper similarity every dimension has the same weight and features within a dimension are averaged,
so ten vocabulary features cannot outvote rhythm. A profile takes at most two traits per dimension. Today the DNA
leans on text: rhythm and voice need recordings of the whole corpus.

## 1. Rhymes

| Feature | Status | Notes |
|---|---|---|
| Rhyme length | in use | ICC 0.57 |
| Multisyllabic rhymes (≥ 3 syllables) | in use | ICC 0.52 |
| Rhymed lines | in use | ICC 0.29 |
| Exact rhymes | in use | ICC 0.29; the era explains 21% |
| Rhyme density | in use | Raplyzer method; ICC 0.27 |
| Internal rhymes above chance | in use | chance control built in |
| Rich and grammatical rhymes | computed | no validation yet |
| Rhyme schemes (AABB, ABAB, monorhyme) | computed | classification not checked by hand |
| Internal rhymes, line by line | planned | best method F1 76.5 against reference annotations ([internal-rhymes.md](internal-rhymes.md)) |
| Position of rhymes in the bar | planned | works on 20 recordings; needs the whole corpus recorded |
| Consonance and in-word rhymes, shifted stress | off | precision 0–46% or at chance level |

## 2. Rhythm and flow (recordings)

| Feature | Status | Notes |
|---|---|---|
| Tempo (BPM) | planned | beat tracking works on 20 songs |
| Syllables per second and per beat | planned | from aligned syllables |
| Stresses on and off the beat, syncopation | planned | from stress and bar positions |
| Double-time, triplets | planned | fit to a 16 vs 12 grid |
| Flow changes within a verse | planned | rhythm similarity of consecutive bars |
| Phrases against bars, pauses | planned | replaces the text-based enjambment |
| Microtiming (ahead of / behind the beat) | hard | the audible difference is close to the alignment error |

## 3. Voice and delivery

| Feature | Status | Notes |
|---|---|---|
| Ad-libs | in use | ICC 0.20 |
| Melodiousness (rapping ↔ singing) | planned | pitch tracking on separated vocals |
| Loudness dynamics | planned | depends on mixing and mastering |
| Timbre, articulation, autotune | hard | nothing to check against |

## 4. Vocabulary and language

| Feature | Status | Notes |
|---|---|---|
| Vocabulary, lexical variety (MATTR) | in use | MATTR ICC 0.23 |
| Syllables per line | in use | ICC 0.31 |
| Word length | in use | ICC 0.20 |
| English words | in use | ICC 0.11, reliability 0.84 |
| Rare words | in use | ICC 0.12 |
| Vulgarisms | computed | ICC 0.20 |
| Slang | computed | ICC 0.06, depends on the song |
| Out-of-dictionary words | computed | a mix of coinages, slang, loans and typos; to be categorised |
| Tense and mood | computed | ICC 0.08 |
| Function-word profile (stylometry) | computed | single words ICC 0.01–0.20 |
| Diminutives | off | suffix rules are wrong in about half of the cases |

## 5. Figures and repetition

| Feature | Status | Notes |
|---|---|---|
| Phrase repetition | in use | ICC 0.13 |
| Similes | in use | ICC 0.14 |
| Repetitiveness (compression) | in use | ICC 0.17 |
| Favourite phrases | computed | examples, not a number |
| Anaphora, epiphora, alliteration | computed | detected well, but depend on the song (ICC 0.01–0.07) |
| Wordplay, punchlines, metaphors | hard | examples only |
| Parallelism, enjambment, onomatopoeia | off | precision ≤ 46% |

## 6. Content

| Feature | Status | Notes |
|---|---|---|
| Perspective | computed | 37/40 correct |
| References | computed | precision 87% |
| Topics | computed | 72% of fragments fit their topic |
| Vocabulary domains | computed | accuracy in context not measured |
| Mode (story, boast, introspection, commentary) | planned | per-verse labels, checked on a sample |
| Emotions | hard | no reference labels for rap |

## 7. Song structure and collaboration

| Feature | Status | Notes |
|---|---|---|
| Chorus share | in use | ICC 0.33 |
| Lines per verse | in use | ICC 0.19 |
| Guests, the rapper's share of a song, intro / outro | computed | depend on the song |
| Producers | computed | Genius metadata (78–100% of songs) |
| Collaboration network | computed | for a map of the scene |
| Beat type (boom-bap, trap…) | planned | a pretrained music-style model, checked on rated beats |

## 8. Context (for interpretation, not similarity)

| Feature | Status | Notes |
|---|---|---|
| Release year, era | in use | explains ≤ 12% of variation for most features |
| Release pace, album length | planned | metadata |
| Popularity | planned | not a style feature |
