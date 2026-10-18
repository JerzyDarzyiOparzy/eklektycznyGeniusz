# Roadmap

## Recordings

The text says nothing about rhythm, and rhythm is where styles differ most in the music-theory literature. A working
audio pipeline exists (`rapdna audio <song_id>`, `src/rapdna/audio/`):

1. download the album version from YouTube (yt-dlp);
2. separate the vocals (Demucs);
3. align the known lyrics to the vocals (torchaudio MMS forced alignment), giving the time of every word and syllable;
4. track beats and bars (beat_this), giving the bar position of every syllable.

On 20 songs, word timing and beats were confirmed by ear and the alignment confidence of verses is 0.64–0.91. The
recording can also choose between a Polish and an English reading of a word, but rappers often use a third, mixed
pronunciation, so such decisions are only candidates for a listening check.

Next steps, all of which need the whole corpus recorded (about 13 hours of processing, about 0.2 MB of results per
song when only the results and compressed vocals are kept):

- syllables per second and per beat, double-time and triplets;
- stresses on and off the beat, the position of rhymes in the bar;
- flow changes within a verse, phrases against bars, pauses;
- melodiousness (pitch of the vocals), later microtiming.

## A larger corpus

60–100 rappers with all studio albums, chosen by the same criteria with balanced decades: the „Antologia Polskiego
Rapu” list on Genius plus the most viewed rappers of every decade. Recordings for a sample.

## Studies to replicate on Polish rap

| Claim from English-language rap | How to test it here |
|---|---|
| Songs differ more than rappers (MCFlow) | done for 20 rappers ([reliability.md](reliability.md)); repeat on the larger corpus |
| Rhyme density rose until about 2002 and then dropped slightly; tempo fell | rhyme statistics and tempo by release year |
| End rhymes cluster around the 4th beat | rhyme positions in the bar (already seen on 20 songs) |
| About 4.5 syllables per second; double-time and triplets as flow types | syllable rates and grid fit |
| Strong beats carry „bright” vowels (i, e) more often (Ammirante & Copelli) | vowel × bar position |
| Rappers on one song adapt their flow to each other (Komaniecki) | rhythm similarity of verses in songs with guests |

## Language

- **Word categories.** 2,734 out-of-dictionary forms to be split into coinages, slang, loans and typos, and 4,443
  proper names to be typed (city, brand, rapper…) with corrected pronunciation. Labels from a language model that
  handles Polish well, checked on a sample.
- **Pronunciation models.** A text-to-IPA model fine-tuned on the phonetic dictionary and the pronunciation
  corrections, and a recording-to-IPA model fine-tuned on aligned rap vocals; together they could pick mixed
  pronunciations that the rules miss.
- **Mode** (story, boast, introspection, commentary) per verse.

## Profiles

- Profiles per album, to tell a stable trait from a change of style.
- Equal weights of the style dimensions in rapper similarity and on the scene map.
