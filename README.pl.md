# eklektycznyGeniusz

[English](README.md) | **Polski**

Mierzalne cechy stylu polskiego rapu: rymy, słownictwo, figury stylistyczne, budowa utworu i treść, liczone dla
każdego utworu i każdego rapera. Każda cecha ma opis tego, co mierzy, czego nie mierzy i jak została sprawdzona,
a każdy raper dostaje profil cech, którymi się wyróżnia.

Korpus obejmuje 20 polskich raperów od lat 90. do 2020.: 83 płyty, 1 330 utworów, teksty z Geniusa.

## Najważniejsze

- **Fonetyka polskiego rapu.** IPA dla każdego słowa, z regułami dla angielskich słów w polskich wersach i polskich
  słów w angielskich wersach, angielskich rdzeni z polską końcówką („shotgunem”), skrótowców czytanych literami
  i liczb.
- **Rymy z reguł.** Rym końcowy to najdłuższa wspólna końcówka samogłosek dwóch wersów, obejmująca akcent ostatniego
  słowa, także przez granice słów. Wobec oznaczeń wzorcowych: trafność 97,8%, pokrycie 96,4%. Nic dotyczącego rymu
  nie jest uczone na mierzonych tekstach.
- **Raper czy utwór.** Dla każdej cechy: jaka część różnic między utworami wynika z tego, kto rapuje (ICC). Styl
  okazuje się cechą dorobku: utwory jednego rapera zawsze różnią się bardziej niż raperzy między sobą, a mimo to
  średnia z typowego dorobku jest rzetelna dla większości cech.
- **Profile.** Dla każdego rapera do pięciu wyróżników wyraźnie odległych od mediany korpusu, z przedziałami ufności
  i przykładami.

## Dokumentacja

| | |
|---|---|
| [Przegląd](docs/pl/overview.md) | korpus, przetwarzanie, co mierzymy |
| [Metodologia](docs/pl/methodology.md) | fonetyka, rymy, figury, słownictwo, treść |
| [Walidacja](docs/pl/validation.md) | wzorce i wyniki dla każdej cechy |
| [Rzetelność i profile](docs/pl/reliability.md) | test „raper czy utwór” i budowa profili |
| [Cechy](docs/pl/features.md) | każda cecha ze stanem |
| [Rymy wewnętrzne](docs/pl/internal-rhymes.md) | porównanie metod dla otwartego problemu |
| [Słownik](docs/pl/glossary.md) | środki stylistyczne w rapie |
| [Plan rozwoju](docs/pl/roadmap.md) | nagrania, większy korpus, badania do powtórzenia |

## Repozytorium

```
config/           progi, listy słów, definicje cech, lista raperów
docs/en, docs/pl  dokumentacja po angielsku i po polsku
src/rapdna/
  genius/         klient API Geniusa i pobieranie tekstów
  text/           sekcje i przypisanie zwrotek, tokenizacja, fonetyka, morfologia
  phonology/      sylaby, cechy głosek, wektory brzmienia
  rhymes/         rymy końcowe, linijka z reguł, gęstość rymów, model Hirjee i Browna do porównań
  figures/        figury stylistyczne, kandydaci na gry słów
  stats/          statystyki, rzetelność, profile, tematy
  experiments/    metody rymów wewnętrznych porównane w docs/pl/internal-rhymes.md
  validate/       złote zbiory, kalibracja, ocena na oznaczeniach wzorcowych
  audio/          nagrania: pobieranie, oddzielanie wokalu, bity, wyrównanie tekstu
  site/           strona z profilami i lokalna przeglądarka utworów
tests/
```

## Uruchomienie

Python 3.12 i [uv](https://docs.astral.sh/uv/). Pakiet i komenda nazywają się `rapdna`.

```
uv sync                      # z --extra topics i/lub --extra audio dla embeddingów i nagrań
uv run rapdna download-resources   # słownik fonetyczny z wydania na GitHubie
uv run rapdna info           # sprawdza zasoby w resources/
uv run rapdna fetch          # wymaga GENIUS_TOKEN w .env
uv run rapdna process        # wersy, słowa z IPA, rymy → data/parquet
uv run rapdna figures
uv run rapdna stats
uv run rapdna themes         # wymaga --extra topics
uv run rapdna surface
uv run rapdna textual
uv run rapdna reliability
uv run rapdna profiles       # → site/dna.html
uv run pytest
```

Programy zewnętrzne: [espeak-ng](https://github.com/espeak-ng/espeak-ng) dla słów spoza słownika i ffmpeg dla
nagrań. Teksty, nagrania i dane pośrednie zostają lokalnie.

## Zasoby

| Plik | Stan | Źródło |
|---|---|---|
| `resources/phonetic_dict.parquet` | wymagany, [wydanie](https://github.com/JerzyDarzyiOparzy/eklektycznyGeniusz/releases/tag/phonetic-dictionary-v1) | 1,79 mln polskich form z IPA: lematy z plWordNetu 4.2, formy odmiany z Morfeusza 2 (SGJP), wymowa przekształcona automatycznie na IPA; bez ręcznej weryfikacji |
| `resources/panphon_similarity.csv`, `legal_onsets.json` | wymagane, w repozytorium | policzone z PanPhon i słownika fonetycznego |
| `resources/slownik_miejski.csv` | opcjonalny | hasła z miejski.pl (kolumna `word`); bez niego nie ma cechy „slang” |
| `resources/homonyms_cleaned.json` | opcjonalny | znaczenia z plWordNetu; bez niego nie ma kandydatów na dwuznaczności |

## Licencja

MIT (zob. `LICENSE`). Krótkie cytaty z tekstów w dokumentacji należą do ich autorów i są użyte jako cytaty; licencja
ich nie obejmuje. `resources/panphon_similarity.csv` jest policzony z [PanPhon](https://github.com/dmort27/panphon)
(MIT).
