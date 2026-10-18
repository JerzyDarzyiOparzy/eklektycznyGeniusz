# Overview

The project turns the lyrics of Polish rappers into measurable style features and describes each rapper by the
features in which they differ from the others. Every number comes with a description of what it measures, what it
does not measure and how it was checked.

## Corpus

| | |
|---|---|
| Rappers | 20, from the 1990s to the 2020s |
| Albums | 83 |
| Songs | 1,330 |
| Source | lyrics and metadata from Genius |

Selection criteria: at least two solo albums and at least 8,000 words in the rapper's own verses; a spread of decades
and regions. The list is in `config/artists.yaml`.

Only lines attributed to the rapper are counted (Genius section headers decide who performs a verse), a chorus counts
once, and songs that repeat text already seen for the same rapper (compilations, alternative versions) are skipped.

## Pipeline

```
Genius lyrics
  → sections and performers            text/sections.py
  → words, word language, IPA          text/phonetics.py
  → lemmas and morphology              text/nlp.py (spaCy)
  → syllables, stress, rhyme units     phonology/, rhymes/match.py
  → rhymes and figures per line        rhymes/end.py, rhymes/ruler_corpus.py, figures/
  → features per song and per rapper   stats/
  → rapper-vs-song reliability         stats/reliability.py
  → distinguishing profiles            stats/profile.py → site/dna.html
```

Each step writes its result to `data/` (Parquet and CSV), so the later steps can be rerun on their own. The commands
are listed in the README.

## What is measured

| Dimension | Features |
|---|---|
| Rhymes | rhyme length, multisyllabic rhymes, rhymed lines, exact rhymes, rhyme density, internal rhymes above chance, rhyme schemes |
| Vocabulary and language | unique lemmas, lexical variety (MATTR), word length, syllables per line, English words, slang, vulgarisms, rare and out-of-dictionary words, tense and mood |
| Figures and repetition | phrase repetition, similes, repetitiveness, anaphora, epiphora, alliteration |
| Content | topics, perspective (I / we / you / they), references, vocabulary domains |
| Song structure | chorus share, verse length, guests, producers, ad-libs |

Details: [methodology.md](methodology.md). Status of every feature: [features.md](features.md).

## Results

- **Profiles.** For every rapper, up to five features in which they stand out, each with a confidence interval, a
  rank among the 20 rappers and examples (`rapdna profiles` → `site/dna.html`).
- **Reliability.** A rapper's style is a property of the catalogue, not of a single song: for every feature, songs
  by one rapper differ more than rappers do, but the mean over a typical catalogue is reliable for most features
  ([reliability.md](reliability.md)).
- **Rhymes.** End rhymes are detected with 97.8% precision and 96.4% recall against reference annotations; internal
  rhymes remain an open problem ([internal-rhymes.md](internal-rhymes.md)).

## Data and copyright

Lyrics, recordings and intermediate data stay local and are not part of the repository. Pages show only numbers and
short fragments as examples.
