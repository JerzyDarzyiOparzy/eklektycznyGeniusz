# Metodologia

## Zasady

- **Reguły, nie modele uczone na raperach.** Rymy oceniają jawne reguły i cechy głosek. Nic dotyczącego rymu nie
  jest uczone na mierzonych tekstach, więc dodanie rapera nie zmienia tego, jak mierzymy pozostałych.
- **Najpierw walidacja, potem porównania.** Cecha trafia do porównań dopiero po sprawdzeniu na wzorcu (zob.
  [validation.md](validation.md)). Słabe cechy liczymy dalej, ale poza porównaniami.
- **Kontrola przypadku.** Tam, gdzie cecha może powstać przypadkiem (rymy, powtórzenia), porównujemy ją z tym samym
  pomiarem na losowych wersach z różnych utworów.

## Od tekstu do brzmienia

1. **Tekst.** Zwrotki przypisane raperowi, refreny liczone raz, stopka Geniusa i ad-liby w nawiasach usunięte
   (ad-liby liczymy osobno).
2. **Język słowa** (`config/word_language.yaml`). W polskim wersie słowo czytamy po angielsku, gdy po angielsku jest
   wyraźnie częstsze („beat”, „trap”, „hype”), chyba że jest na liście polskich słów i zapożyczeń („won”, „fury”,
   „bus”). W angielskim wersie słowo prawie nieznane po angielsku czytamy po polsku („jej”, „że”). Angielskie rdzenie
   z polską końcówką („shotgunem”) czytamy jako hybrydy, a sąsiednie słowa angielskiej frazy idą za nią („I'll be
   back”, „Frank Castle”). Częstości pochodzą z wordfreq.
3. **Wymowa (IPA).** W kolejności: wyjątki (`config/pronunciation_exceptions.yaml`), polski słownik fonetyczny
   (1,79 mln form: lematy z plWordNetu 4.2, formy odmiany z Morfeusza 2, wymowa przekształcona automatycznie na IPA,
   bez ręcznej weryfikacji), eSpeak NG. Angielskie głoski sprowadzamy do najbliższych polskich, tak jak
   wymawia je polski raper. Skrótowce, których nie da się przeczytać jak słowa, czytamy literami („WKU”), liczby
   zapisujemy słownie.
4. **Sylaby i akcent.** Granica sylaby według zasady maksymalnego nagłosu; akcent ze słownika albo z eSpeak,
   a w braku danych na przedostatniej sylabie.
5. **Klocki rymowe.** Wers to ciąg klocków: samogłoska plus spółgłoski do następnej samogłoski, ponad granicami słów.
   „polskie tango” → `[ɔlsk] [ɛt] [aŋɡ] [ɔ]`. Cięcie wypada przed samogłoską, więc wynik nie zależy od tego, gdzie
   w zbitce spółgłosek leży granica sylaby.

## Rymy końcowe

Rym końcowy dwóch wersów (do trzech wersów odstępu w zwrotce) to ich **najdłuższa wspólna końcówka samogłosek, która
obejmuje akcent ostatniego słowa po obu stronach** (`rhymes/end.py`). Bliskie samogłoski liczą się jako jedna
(y = i, ę = e, ą = o). Końcówka może biec przez kilka słów, więc „polskie tango / grząskie bagno” to rym
czterosylabowy. Te same słowa po obu stronach to epifora, nie rym; krótkie słowo wiszące na końcu wersu („…moskitierę
i”) pomijamy.

Każdy rym opisujemy na osiach ze [słownika](glossary.md):

| Oś | Wartości |
|---|---|
| dokładność | dokładny (zgadzają się też spółgłoski końcówki) albo asonansowy |
| długość | liczba sylab wspólnej końcówki |
| bogactwo | bogaty, gdy zgadza się spółgłoska przed samogłoską akcentowaną („rama / brama”) |
| materiał | gramatyczny, gdy oba słowa mają tę samą część mowy i wspólną końcówkę fleksyjną („zrobiłem / kupiłem”), w przeciwnym razie leksykalny |

Z tego wynikają statystyki: średnia długość rymu, udział rymów co najmniej trzysylabowych, udział wersów
zrymowanych, udział rymów dokładnych oraz układy rymów w kolejnych czwórkach wersów (AABB, ABAB, monorym).

## Linijka z reguł

Do rymów w dowolnym miejscu wersu dwa wersy porównujemy klocek po klocku wzdłuż każdej przekątnej tabeli
klocki × klocki (`rhymes/rules.py`, `rhymes/match.py`).

| Samogłoski | Ocena |
|---|---|
| te same | +2 |
| e / ę, o / ą | +1,5 |
| i / y | +1 |
| inne | przerywają rym |

Zbitki spółgłosek wyrównujemy tak, żeby suma była najwyższa: ta sama spółgłoska +2, różne
`2 − 8 × (1 − podobieństwo PanPhon)`, spółgłoska bez pary −1. Rym to ciąg klocków o sumie powyżej progu
skalibrowanego na oznaczonym złotym zbiorze. Linijki używamy do:

- **rymów wewnętrznych ponad przypadek**: udział par sąsiednich wersów z rymem kończącym się w środku wersu minus ten
  sam udział w losowych parach własnych wersów rapera z różnych utworów (sama liczba to głównie przypadek);
- kontroli przypadku przy układach rymów;
- `rapdna rhymes-for`: co rymuje się z podanym słowem.

## Gęstość rymów

Dla każdego słowa najdłuższy ciąg samogłosek wspólny z jednym z 15 poprzednich słów, uśredniony po słowach (metoda
Raplyzera, Malmi i in. 2016). Liczy też przypadkowe zbieżności, więc sens mają tylko różnice między raperami.

## Figury

| Figura | Reguła |
|---|---|
| Powtórzenie frazy | ciąg co najmniej dwóch różnych słów powtarza się w wersie albo wraca z poprzedniego wersu |
| Anafora / epifora | sąsiednie wersy zaczynają / kończą się tym samym słowem (bez „i / a / bo / że”, bez ech) |
| Aliteracja | co najmniej trzy kolejne słowa treściowe zaczynają się tą samą głoską |
| Porównania | „jak”, „niczym”, „jakby”, „niby” z rzeczownikiem, nazwą albo przymiotnikiem |
| Gry słów | kandydaci z adnotacji fanów, homofonów, znaczeń ze Słowosieci i wektorów brzmienia; pokazujemy tylko potwierdzone, jako przykłady |

## Słownictwo i język

| Cecha | Jak liczona |
|---|---|
| Słownictwo | unikalne lematy w 8 000 słów, średnia z 20 losowych kolejności utworów |
| Różnorodność słów | MATTR w przesuwanym oknie 500 słów (100 dla utworu) |
| Długość słów, sylaby na wers | z transkrypcji fonetycznej |
| Słowa angielskie | udział słów czytanych po angielsku |
| Słowa rzadkie | udział polskich słów o częstości Zipf w wordfreq poniżej 3 |
| Słowa spoza słowników | polskie formy, których nie ma w słowniku i prawie nie zna wordfreq (słowotwórstwo, slang, zapożyczenia, literówki) |
| Slang | hasła Słownika Miejskiego spoza słownika ogólnego i nieczęste w ogólnej polszczyźnie |
| Wulgaryzmy | rdzenie z `config/vulgarisms.yaml` |
| Czas i tryb | morfologia spaCy: przeszły, teraźniejszy, przyszły, tryb rozkazujący |
| Powtarzalność | rozmiar skompresowanych wersów rapera w utworze do rozmiaru surowego |

## Treść

| Cecha | Jak liczona |
|---|---|
| Tematy | fragmenty zwrotek do czterech wersów zamienione na wektory mmlw-roberta-large i pogrupowane BERTopic; skupiska nazwane ręcznie |
| Perspektywa | udział 1. os. l.poj., 1. os. l.mn., 2. os. i 3. os. l.mn. wśród zaimków i czasowników z oznaczoną osobą |
| Odniesienia | nazwy własne (NER spaCy, z filtrami) i ksywy innych raperów z korpusu na 1000 słów |
| Dziedziny słownictwa | słowa z ręcznie spisanych słowników sportu, wojny, jedzenia, religii i gier na 1000 słów |

## Budowa utworu

Z nagłówków sekcji i metadanych Geniusa: długość utworu w wersach, udział refrenu, wersy na zwrotkę, intro i outro,
goście, udział rapera w utworze, producenci, ad-liby (fragmenty w nawiasach w surowym tekście), wymienianie własnej
ksywy i ulubione zwroty (ciągi słów w co najmniej trzech utworach rapera, rzadkie u innych).

## Punkt odniesienia

Model Hirjee i Browna (log-odds par głosek uczone na korpusie, `rhymes/hb.py`) zostaje tylko do porównań.
