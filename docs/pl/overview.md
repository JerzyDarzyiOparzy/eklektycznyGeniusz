# Przegląd

Projekt zamienia teksty polskich raperów na mierzalne cechy stylu i opisuje każdego rapera tymi cechami, którymi
różni się od pozostałych. Każda liczba ma opis: co mierzy, czego nie mierzy i jak została sprawdzona.

## Korpus

| | |
|---|---|
| Raperzy | 20, od lat 90. do 2020. |
| Płyty | 83 |
| Utwory | 1 330 |
| Źródło | teksty i metadane z Geniusa |

Kryteria doboru: co najmniej dwie płyty solowe i co najmniej 8 000 słów we własnych zwrotkach; rozrzut dekad
i regionów. Lista jest w `config/artists.yaml`.

Liczymy tylko wersy przypisane raperowi (o wykonawcy zwrotki decydują nagłówki sekcji na Geniusie), refren liczy się
raz, a utwory powtarzające tekst już widziany u tego samego rapera (składanki, wersje alternatywne) są pomijane.

## Przetwarzanie

```
teksty z Geniusa
  → sekcje i wykonawcy                 text/sections.py
  → słowa, język słowa, IPA            text/phonetics.py
  → lematy i morfologia                text/nlp.py (spaCy)
  → sylaby, akcent, klocki rymowe      phonology/, rhymes/match.py
  → rymy i figury w wersach            rhymes/end.py, rhymes/ruler_corpus.py, figures/
  → cechy utworów i raperów            stats/
  → test „raper czy utwór”             stats/reliability.py
  → profile wyróżników                 stats/profile.py → site/dna.html
```

Każdy krok zapisuje wynik w `data/` (Parquet i CSV), więc późniejsze kroki da się przeliczyć osobno. Komendy są
w README.

## Co mierzymy

| Wymiar | Cechy |
|---|---|
| Rymy | długość rymu, rymy wielosylabowe, wersy zrymowane, rymy dokładne, gęstość rymów, rymy wewnętrzne ponad przypadek, układy rymów |
| Słownictwo i język | unikalne lematy, różnorodność słów (MATTR), długość słów, sylaby na wers, słowa angielskie, slang, wulgaryzmy, słowa rzadkie i spoza słowników, czas i tryb |
| Figury i powtórzenia | powtórzenia fraz, porównania, powtarzalność, anafory, epifory, aliteracje |
| Treść | tematy, perspektywa (ja / my / ty / oni), odniesienia, dziedziny słownictwa |
| Budowa utworu | udział refrenu, długość zwrotki, goście, producenci, ad-liby |

Szczegóły: [methodology.md](methodology.md). Stan każdej cechy: [features.md](features.md).

## Wyniki

- **Profile.** Dla każdego rapera do pięciu cech, którymi się wyróżnia, każda z przedziałem ufności, miejscem wśród
  20 raperów i przykładami (`rapdna profiles` → `site/dna.html`).
- **Rzetelność.** Styl rapera to cecha dorobku, nie pojedynczego utworu: dla każdej cechy utwory jednego rapera
  różnią się bardziej niż raperzy między sobą, ale średnia z typowego dorobku jest rzetelna dla większości cech
  ([reliability.md](reliability.md)).
- **Rymy.** Rymy końcowe wykrywamy z trafnością 97,8% i pokryciem 96,4% wobec oznaczeń wzorcowych; rymy wewnętrzne
  pozostają otwartym problemem ([internal-rhymes.md](internal-rhymes.md)).

## Dane i prawa autorskie

Teksty, nagrania i dane pośrednie zostają lokalnie i nie są częścią repozytorium. Strony pokazują tylko liczby
i krótkie fragmenty jako przykłady.
