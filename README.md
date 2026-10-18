# eklektycznyGeniusz

**English** | [Polski](README.pl.md)

Measurable style features of Polish rap lyrics: rhymes, vocabulary, stylistic figures, song structure and content,
computed per song and per rapper. Every feature states what it measures, what it does not measure and how it was
validated, and every rapper gets a profile of the features in which they stand out.

The corpus covers 20 Polish rappers from the 1990s to the 2020s: 83 albums, 1,330 songs, lyrics from Genius.

## Highlights

- **Phonetics for Polish rap.** IPA for every word, with rules for English words in Polish lines and Polish words in
  English lines, English stems with Polish endings („shotgunem”), spelled-out acronyms and numbers.
- **Rule-based rhymes.** An end rhyme is the longest shared vowel tail of two lines covering the stress of the last
  word, across word boundaries. Against reference rhyme annotations: 97.8% precision, 96.4% recall. Nothing about
  rhyme is learned from the lyrics being measured.
- **Rapper or song.** For every feature, the share of song-to-song variation that comes from who is rapping (ICC).
  A style turns out to be a property of the catalogue: songs by one rapper always differ more than rappers do, yet the
  mean over a typical catalogue is reliable for most features.
- **Profiles.** For each rapper, up to five traits that are clearly away from the corpus median, with confidence
  intervals and examples.

## Documentation

| | |
|---|---|
| [Overview](docs/en/overview.md) | corpus, pipeline, what is measured |
| [Methodology](docs/en/methodology.md) | phonetics, rhymes, figures, vocabulary, content |
| [Validation](docs/en/validation.md) | references and results for every feature |
| [Reliability and profiles](docs/en/reliability.md) | the rapper-vs-song test and how profiles are built |
| [Features](docs/en/features.md) | every feature with its status |
| [Internal rhymes](docs/en/internal-rhymes.md) | methods compared on an open problem |
| [Glossary](docs/en/glossary.md) | stylistic devices in rap |
| [Roadmap](docs/en/roadmap.md) | recordings, a larger corpus, studies to replicate |

## Repository

```
config/           thresholds, word lists, feature definitions, rapper list
docs/en, docs/pl  documentation in English and Polish
src/rapdna/
  genius/         Genius API client and lyrics scraper
  text/           sections and attribution, tokenisation, phonetics, morphology
  phonology/      syllables, phoneme features, sound vectors
  rhymes/         end rhymes, the rule-based rhyme ruler, rhyme density, a Hirjee & Brown baseline
  figures/        stylistic figures, wordplay candidates
  stats/          statistics, reliability, profiles, topics
  experiments/    internal-rhyme methods compared in docs/en/internal-rhymes.md
  validate/       gold sets, calibration, evaluation against reference annotations
  audio/          recordings: download, vocal separation, beats, forced alignment
  site/           profile page and a local song browser
tests/
```

## Running

Python 3.12 and [uv](https://docs.astral.sh/uv/). The package and its command are called `rapdna`.

```
uv sync                      # add --extra topics and/or --extra audio for embeddings and recordings
uv run rapdna download-resources   # the phonetic dictionary, from the GitHub release
uv run rapdna info           # checks the resources in resources/
uv run rapdna fetch          # needs GENIUS_TOKEN in .env
uv run rapdna process        # lines, words with IPA, rhymes → data/parquet
uv run rapdna figures
uv run rapdna stats
uv run rapdna themes         # needs --extra topics
uv run rapdna surface
uv run rapdna textual
uv run rapdna reliability
uv run rapdna profiles       # → site/dna.html
uv run pytest
```

External tools: [espeak-ng](https://github.com/espeak-ng/espeak-ng) for words missing from the dictionary, and ffmpeg
for recordings. Lyrics, recordings and intermediate data stay local.

## Resources

| File | Status | Source |
|---|---|---|
| `resources/phonetic_dict.parquet` | required, [release](https://github.com/JerzyDarzyiOparzy/eklektycznyGeniusz/releases/tag/phonetic-dictionary-v1) | 1.79 million Polish word forms with IPA: lemmas from plWordNet 4.2, inflected forms from Morfeusz 2 (SGJP), converted to IPA automatically; not verified by hand |
| `resources/panphon_similarity.csv`, `legal_onsets.json` | required, in the repository | computed from PanPhon and the phonetic dictionary |
| `resources/slownik_miejski.csv` | optional | headwords of miejski.pl (column `word`); without it there is no slang feature |
| `resources/homonyms_cleaned.json` | optional | plWordNet senses; without it there are no polysemy candidates |

## License

MIT (see `LICENSE`). Short quotes from lyrics in the documentation belong to their authors and are used as
quotations; they are not covered by the license. `resources/panphon_similarity.csv` is computed from
[PanPhon](https://github.com/dmort27/panphon) (MIT).
