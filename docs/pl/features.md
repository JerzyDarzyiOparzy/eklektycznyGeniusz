# Cechy

Wszystko, co może opisać styl rapera, w ośmiu wymiarach, ze stanem każdej cechy.

**Stan:** **w użyciu**: zwalidowana, w porównaniach i profilach; **liczona**: liczona, poza porównaniami do czasu
walidacji; **zaplanowana**: dane albo metoda są, jeszcze nie liczona; **trudna**: możliwa, ale o niepewnej jakości
albo bez wzorca do sprawdzenia; **wyłączona**: sprawdzona i za słaba.

**Równowaga.** W podobieństwie raperów każdy wymiar ma tę samą wagę, a cechy w wymiarze są uśredniane, więc dziesięć
cech słownictwa nie przegłosuje rytmu. Profil bierze najwyżej dwa wyróżniki na wymiar. Dziś DNA opiera się na tekście:
rytm i głos wymagają nagrań całego korpusu.

## 1. Rymy

| Cecha | Stan | Uwagi |
|---|---|---|
| Długość rymu | w użyciu | ICC 0,57 |
| Rymy wielosylabowe (≥ 3 sylaby) | w użyciu | ICC 0,52 |
| Wersy zrymowane | w użyciu | ICC 0,29 |
| Rymy dokładne | w użyciu | ICC 0,29; epoka wyjaśnia 21% |
| Gęstość rymów | w użyciu | metoda Raplyzera; ICC 0,27 |
| Rymy wewnętrzne ponad przypadek | w użyciu | kontrola przypadku wbudowana w miarę |
| Rymy bogate i gramatyczne | liczona | bez walidacji |
| Układy rymów (AABB, ABAB, monorym) | liczona | klasyfikacja niesprawdzona ręcznie |
| Rymy wewnętrzne, wers po wersie | zaplanowana | najlepsza metoda F1 76,5 wobec oznaczeń wzorcowych ([internal-rhymes.md](internal-rhymes.md)) |
| Położenie rymów w takcie | zaplanowana | działa na 20 nagraniach; wymaga nagrań całego korpusu |
| Rymy konsonansowe i wewnątrzwyrazowe, przesunięty akcent | wyłączona | trafność 0–46% albo poziom przypadku |

## 2. Rytm i flow (nagrania)

| Cecha | Stan | Uwagi |
|---|---|---|
| Tempo (BPM) | zaplanowana | wykrywanie bitów działa na 20 utworach |
| Sylaby na sekundę i na bit | zaplanowana | z sylab wyrównanych w czasie |
| Akcenty na bicie i poza nim, synkopy | zaplanowana | z akcentów i pozycji w takcie |
| Double-time, triole | zaplanowana | dopasowanie do siatki 16 i 12 |
| Zmiany flow w zwrotce | zaplanowana | podobieństwo rytmu kolejnych taktów |
| Frazy a takty, pauzy | zaplanowana | zastępuje przerzutnie liczone z tekstu |
| Mikrotiming (przed bitem / za bitem) | trudna | słyszalna różnica jest bliska błędowi wyrównania |

## 3. Głos i wykonanie

| Cecha | Stan | Uwagi |
|---|---|---|
| Ad-liby | w użyciu | ICC 0,20 |
| Melodyjność (rapowanie ↔ śpiew) | zaplanowana | wysokość głosu na oddzielonym wokalu |
| Dynamika głośności | zaplanowana | zależy od miksu i masteringu |
| Barwa, artykulacja, autotune | trudna | brak wzorca |

## 4. Słownictwo i język

| Cecha | Stan | Uwagi |
|---|---|---|
| Słownictwo, różnorodność słów (MATTR) | w użyciu | MATTR ICC 0,23 |
| Sylaby na wers | w użyciu | ICC 0,31 |
| Długość słów | w użyciu | ICC 0,20 |
| Słowa angielskie | w użyciu | ICC 0,11, rzetelność 0,84 |
| Słowa rzadkie | w użyciu | ICC 0,12 |
| Wulgaryzmy | liczona | ICC 0,20 |
| Slang | liczona | ICC 0,06, zależy od utworu |
| Słowa spoza słowników | liczona | mieszanka słowotwórstwa, slangu, zapożyczeń i literówek; do podziału na kategorie |
| Czas i tryb | liczona | ICC 0,08 |
| Profil słów funkcyjnych (stylometria) | liczona | pojedyncze słowa ICC 0,01–0,20 |
| Zdrobnienia | wyłączona | reguły końcówek mylą się w około połowie przypadków |

## 5. Figury i powtórzenia

| Cecha | Stan | Uwagi |
|---|---|---|
| Powtórzenia fraz | w użyciu | ICC 0,13 |
| Porównania | w użyciu | ICC 0,14 |
| Powtarzalność (kompresja) | w użyciu | ICC 0,17 |
| Ulubione zwroty | liczona | przykłady, nie liczba |
| Anafory, epifory, aliteracje | liczona | wykrywane dobrze, ale zależą od utworu (ICC 0,01–0,07) |
| Gry słów, pancze, metafory | trudna | tylko przykłady |
| Paralelizmy, przerzutnie, onomatopeje | wyłączona | trafność ≤ 46% |

## 6. Treść

| Cecha | Stan | Uwagi |
|---|---|---|
| Perspektywa | liczona | 37/40 trafnych |
| Odniesienia | liczona | trafność 87% |
| Tematy | liczona | 72% fragmentów pasuje do tematu |
| Dziedziny słownictwa | liczona | trafność w kontekście niezmierzona |
| Tryb wypowiedzi (opowieść, przechwałka, introspekcja, komentarz) | zaplanowana | etykiety na zwrotkę, sprawdzone na próbce |
| Emocje | trudna | brak wzorcowych etykiet dla rapu |

## 7. Budowa utworu i współpraca

| Cecha | Stan | Uwagi |
|---|---|---|
| Udział refrenu | w użyciu | ICC 0,33 |
| Wersy na zwrotkę | w użyciu | ICC 0,19 |
| Goście, udział rapera w utworze, intro / outro | liczona | zależą od utworu |
| Producenci | liczona | metadane Geniusa (78–100% utworów) |
| Sieć współpracy | liczona | do mapy sceny |
| Typ bitu (boom-bap, trap…) | zaplanowana | gotowy model stylów muzycznych, sprawdzony na ocenionych bitach |

## 8. Kontekst (do interpretacji, nie do podobieństwa)

| Cecha | Stan | Uwagi |
|---|---|---|
| Rok wydania, epoka | w użyciu | wyjaśnia ≤ 12% zmienności większości cech |
| Tempo wydawania, długość płyt | zaplanowana | metadane |
| Popularność | zaplanowana | to nie cecha stylu |
