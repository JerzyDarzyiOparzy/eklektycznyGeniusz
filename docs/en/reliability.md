# Rapper or song? Reliability and profiles

## The question

A statistic describes a rapper only if the rapper's songs resemble each other more than they resemble other
rappers' songs. Studies of English-language rap (MCFlow; Condit-Schultz, Ohriner) found that songs by one rapper often
differ more than rappers do. The same is tested here.

## Method

Every feature is computed separately for every song with at least 24 of the rapper's lines: 1,019 songs, 20 rappers,
a median of 44 songs per rapper (`stats/reliability.py`).

- **ICC**: the share of the variation between songs that comes from who is rapping (1 = only the rapper, 0 = only
  the song); one-way random model for unequal groups, with a 95% interval from leaving out one rapper at a time.
- **eta²**: the share of variation explained by the rapper and by the decade of release.
- **Songs needed**: how many songs a rapper's mean needs to reach reliability 0.8 (Spearman–Brown).
- **Reliability at 44 songs**: the reliability of the mean at the median catalogue size.

## Results

| Feature | ICC (95%) | eta² rapper / decade | Songs for 0.8 | Reliability at 44 songs |
|---|---|---|---|---|
| Rhyme length | 0.57 (0.16–0.98)¹ | 0.57 / 0.11 | 3 | 0.98 |
| Rhymes of ≥ 3 syllables | 0.52 (0.21–0.84)¹ | 0.52 / 0.12 | 4 | 0.98 |
| Chorus share | 0.33 (0.21–0.46) | 0.33 / 0.17 | 8 | 0.96 |
| Syllables per line | 0.31 (0.14–0.48) | 0.31 / 0.04 | 9 | 0.95 |
| Rhymed lines | 0.29 (0.13–0.46) | 0.30 / 0.10 | 10 | 0.95 |
| Exact rhymes | 0.29 (0.12–0.46) | 0.29 / 0.21 | 10 | 0.95 |
| Rhyme density | 0.27 (0.08–0.47) | 0.28 / 0.04 | 11 | 0.94 |
| Lexical variety (MATTR) | 0.23 (0.11–0.36) | 0.24 / 0.08 | 13 | 0.93 |
| Ad-libs | 0.20 (0.11–0.30) | 0.21 / 0.09 | 16 | 0.92 |
| Word length | 0.20 (0.03–0.36) | 0.20 / 0.00 | 16 | 0.92 |
| Vulgarisms | 0.20 (0.06–0.33) | 0.20 / 0.03 | 16 | 0.92 |
| Lines per verse | 0.19 (0.09–0.30) | 0.20 / 0.06 | 17 | 0.91 |
| Repetitiveness | 0.17 (0.09–0.26) | 0.18 / 0.08 | 19 | 0.90 |
| Similes | 0.14 (0.05–0.23) | 0.15 / 0.03 | 25 | 0.88 |
| Phrase repetition | 0.13 (0.07–0.18) | 0.14 / 0.07 | 28 | 0.86 |
| Rare words | 0.12 (0.00–0.23) | 0.13 / 0.02 | 30 | 0.86 |
| English words | 0.11 (0.03–0.19) | 0.12 / 0.07 | 32 | 0.84 |
| Imperatives | 0.08 | 0.10 / 0.03 | 44 | 0.80 |
| Past tense | 0.08 | 0.09 / 0.05 | 46 | 0.79 |
| Epiphora | 0.07 | 0.08 / 0.01 | 56 | 0.76 |
| Slang | 0.06 | 0.08 / 0.00 | 59 | 0.75 |
| Self-mentions | 0.05 | 0.06 / 0.05 | 78 | 0.69 |
| Anaphora | 0.02 | 0.04 / 0.02 | 177 | 0.50 |
| Alliteration | 0.01 | 0.03 / 0.01 | 350 | 0.33 |

¹ Driven by one rapper with very long rhymes (mean 4.25 syllables); without that rapper the ICC is about 0.36.

## What follows

1. For **every** feature, songs by one rapper differ more than rappers do (ICC below 0.6). A style is a property of a
   catalogue, not of a verse.
2. The mean over a whole catalogue is still reliable: at 44 songs most features reach 0.8 or more.
3. Anaphora, alliteration, epiphora, self-mentions and slang depend mainly on the song. They stay as statistics, but
   do not enter the profiles.
4. Album comparisons (about 10 songs) are trustworthy only for features with an ICC of about 0.28 or more.
5. The decade explains little (eta² ≤ 0.12), except for the share of exact rhymes (0.21).
6. A song has about 40 lines, so part of the song-to-song variation is measurement noise; the ICC is a lower bound.

## Profiles

A profile lists the features in which a rapper stands out (`stats/profile.py`, `config/profile.yaml`):

1. The rapper's value is the word-weighted mean over their songs.
2. A robust z-score against the other rappers: (value − median) / (1.4826 · MAD).
3. A 95% interval from resampling the rapper's songs (bootstrap, 1,000 draws).
4. Reliability of the mean from the ICC and the rapper's number of songs.

A feature becomes a **trait** when |z| ≥ 1, the interval stays on one side of the corpus median and the reliability is
at least 0.8. A profile shows at most two traits per style dimension and five in total, so that one dimension (rhymes,
for example) cannot fill it.
