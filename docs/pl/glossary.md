# Słownik środków stylistycznych w rapie

Każdy środek ma tu jedną definicję; pozostałe dokumenty, strony i kod używają tych nazw.

## Zasady

1. **Jedna definicja na środek.** Definicja mówi, czym środek *jest*, niezależnie od tego, jak go liczymy.
2. **Pomiar może być węższy niż definicja, ale nigdy inny.** Przykład: definicja aliteracji wymaga co najmniej dwóch
   słów, a automat liczy dopiero od trzech, bo dwa słowa na tę samą głoskę zdarzają się przypadkiem. Automat łapie
   więc część aliteracji, ale nie liczy niczego, co aliteracją nie jest.
3. **Brzmienie, nie pisownia.** Środki dźwiękowe oceniamy po wymowie: „chata / hak” i „rzeka / żaba” zaczynają się
   tą samą głoską (`x` i `ʐ`), choć pisze się je inaczej.
4. **Przykłady** pochodzą z korpusu (raper w nawiasie), chyba że są oznaczone *(przykład ogólny)*.

Kolumna **W projekcie**:
- **mierzone**: liczone, zwalidowane i w porównaniach;
- **liczone, poza porównaniami**: liczone bez ręcznej kontroli albo z niepewnym wynikiem;
- **wyłączone**: walidacja wypadła źle; liczone w plikach, ale niepokazywane;
- **kandydaci**: automat wskazuje, decyduje ocena; pokazujemy tylko przykłady;
- **nie mierzone**: poza obecnym zakresem.

---

## 1. Rym

**Rym** to powtórzenie ciągu głosek w dwóch bliskich miejscach tekstu, oparte przede wszystkim na samogłoskach
(albo, w rymie konsonansowym, na spółgłoskach). Powtórzony ciąg ma tyle samo sylab po obu stronach i liczy się
w wymowie, nie w pisowni.

Ciąg może leżeć w dowolnym miejscu wersu: na końcu słowa, w środku słowa, na styku kilku słów. Najczęstszy przypadek,
znany z poezji, to **rym klauzulowy**: ciąg biegnie od ostatniej akcentowanej samogłoski słowa do jego końca, a głoski
przed tą samogłoską się nie liczą („**t**ango / **b**agno”). To jedna z wartości na osi 1.5, a nie osobna definicja.

Rym opisujemy na kilku niezależnych osiach, z jedną wartością na każdej, np. „końcowy, klauzulowy, żeński,
asonansowy, wielokrotny, ubogi, leksykalny”.

### 1.1 Oś: dokładność brzmienia

| Rodzaj | Definicja | Przykład | W projekcie (kod) |
|---|---|---|---|
| **Rym dokładny** | Wszystkie głoski powtórzonego ciągu są identyczne. | „czy już wize**runek** / niszczą nam opat**runek**” (Quebonafide) | mierzone (`exact`) |
| **Rym niedokładny** | Głoski zgadzają się tylko częściowo. Trzy podrodzaje niżej. | | |
| ↳ **rym asonansowy** | Identyczne są samogłoski, spółgłoski się różnią. | „taki mamy **lot** / twardo gramy **rok**” (Kaz Bałagane) | mierzone (`assonance`) |
| ↳ **rym konsonansowy** (pararym) | Identyczne są spółgłoski, samogłoski się różnią. | „**las** / **los**” *(przykład ogólny)* | **wyłączone** (wśród 100 kandydatów ani jednego prawdziwego) |
| ↳ **rym przybliżony** | Różni się co najmniej jedna samogłoska i jedna spółgłoska, ale głoski są tak bliskie, że ucho słyszy rym. | „zamykają się **drzwi** / bo się bałem **żyć**” (Białas): `i`/`y` i brak `ć` | `approx` w linijce z reguł |

Uwaga do nazw: **rym asonansowy** to rodzaj rymu. **Asonans** (2.2) to osobna figura, czyli samogłoska powtarzana
w kilku słowach; w kodzie `assonance_chain`.

### 1.2 Oś: miejsce akcentu

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym męski** | Akcent na ostatniej sylabie, rym zaczyna się w ostatniej sylabie. | „**lot** / **rok**” (Kaz Bałagane), „Jack / I'll be back” (Quebonafide) | nie mierzone osobno |
| **Rym żeński** | Akcent na przedostatniej sylabie, rym ma dwie sylaby. W polszczyźnie to rodzaj podstawowy. | „t**ango** / b**agno**” *(przykład ogólny)* | nie mierzone osobno |
| **Rym daktyliczny** | Akcent na trzeciej sylabie od końca, rym ma trzy sylaby. | „**fi**zyka / **li**ryka” *(przykład ogólny)* | nie mierzone osobno |

### 1.3 Oś: zgodność z akcentem

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym zgodny z akcentem** | Sylaby akcentowane obu stron stoją naprzeciw siebie. | „t**a**ngo / b**a**gno” | linijka z reguł |
| **Rym z przesuniętym akcentem** | Ciąg zgadza się tylko wtedy, gdy jedna strona jest czytana z akcentem w innym miejscu niż w normie. Raper nagina wymowę do rymu. | „szybk**a** / koleg**a**” z akcentem na „-ga” *(przykład ogólny)* | **wyłączone** (kandydaci, często błędy akcentu w słowniku; potwierdzić może tylko nagranie) |

### 1.4 Oś: długość

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Długość rymu** | Liczba sylab powtórzonego ciągu. | | mierzone (`rhyme_length`) |
| **Rym wielokrotny** (wielosylabowy) | Rym o długości **co najmniej 3 sylab**, czyli dłuższy niż podstawowy rym żeński. | „postawy marzyc**ielskiej** / laurki od straży m**iejskiej**” (Taco Hemingway), „wlokę od st**artu** / ochotę do ż**artu**” (Oxon) | mierzone (`three_plus_share`) |

### 1.5 Oś: zakotwiczenie w słowie

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym klauzulowy** | Ciąg kończy się na końcu słowa po obu stronach i zaczyna od samogłoski akcentowanej (albo wcześniej, gdy ciągnie się wstecz przez kolejne słowa). | „p**olskie tango** / gr**ząskie bagno**” | mierzone |
| **Rym wewnątrzwyrazowy** | Ciąg zaczyna się albo kończy w środku słowa po co najmniej jednej stronie. Typowy dla rapu rym wielokrotny „na samogłoskach”, niezwiązany z granicami słów. | „**zakaza**ny owoc / **za kaza**nie to” *(przykład ogólny)* | **wyłączone** (trafność 46%) |

### 1.6 Oś: położenie w wersie

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym końcowy** | Obie strony kończą się na końcu wersu. | „opat**runek** / wize**runek**” wyżej | mierzone (do 3 wersów odstępu) |
| **Rym wewnętrzny** | Co najmniej jedna strona leży wewnątrz wersu. | „**Ogromny** hol, w nim znajduję jakiś **skromny** fotel” (Taco Hemingway) | mierzone jako nadwyżka ponad przypadek (`internal_rhymes_excess`) |

### 1.7 Oś: bogactwo

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym ubogi** | Zgodność zaczyna się dopiero od samogłoski. | „**t**ama / **br**ama” | liczone |
| **Rym bogaty** | Zgadza się też spółgłoska (albo spółgłoski) tuż przed pierwszą samogłoską ciągu. | „b**rama** / **rama**”, „t**rawa** / sp**rawa**” | liczone (`rich_share`) |

### 1.8 Oś: materiał

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym leksykalny** | Rymują się różne rdzenie albo rym wychodzi poza końcówkę odmiany. | „t**ango** / b**agno**” | liczone |
| **Rym gramatyczny** | Słowa tej samej części mowy rymują się tylko wspólną końcówką odmiany albo przyrostkiem („-iłem”, „-ować”, „-ami”). Łatwy, uchodzi za słabszy. | „zrob**iłem** / kup**iłem**” | liczone (`grammatical_share`) |

### 1.9 Oś: budowa

| Rodzaj | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **Rym składany** | Jedna strona rymu składa się z kilku słów, druga z jednego. | „**do mnie** / **skromnie**” *(przykład ogólny)* | nie mierzone osobno (oceniany jak każdy inny rym) |
| **Rym homonimiczny** | Rymują się słowa o identycznym brzmieniu i różnym znaczeniu. Jest jednocześnie grą słów. | „**może** / **morze**” *(przykład ogólny)* | kandydaci (homofony, punkt 4) |
| **Rym tautologiczny** | To samo słowo albo odmiany jednego słowa rymują się ze sobą. | „...ziomal / ...ziomal” (Żabson), „mówić / mówisz” | **nie liczymy jako rymu**; powtórzenie słowa to epifora (3.2) |

### 1.10 Oś: układ w zwrotce

| Rodzaj | Definicja | W projekcie |
|---|---|---|
| **Parzysty** (aabb) | Rymują się kolejne pary wersów. | liczone na czwórkach wersów, poza porównaniami (`scheme_aabb`) |
| **Przeplatany** (abab) | Rymuje się co drugi wers. | liczone, poza porównaniami (`scheme_abab`) |
| **Okalający** (abba) | Pierwszy z czwartym, drugi z trzecim. | liczone, ale na poziomie przypadku (ok. 1%), więc niepokazywane |
| **Monorym** (aaaa…) | Wszystkie wersy zwrotki na jeden rym. Częsty w rapie. | liczone na czwórkach wersów, poza porównaniami (`scheme_monorhyme`) |

Rodziny rymów w całej zwrotce (dowolny schemat, np. ABABCDCD): `src/rapdna/experiments/families.py`, w lokalnej
przeglądarce utworów (`rapdna browser`). Kod układów: `src/rapdna/stats/schemes.py`. Czwórki liczymy od początku
zwrotki; w czwórkach z losowych wersów każdy układ wychodzi poniżej 1%.

### 1.11 Gęstość rymów

To **miara**, nie środek. Dla każdego słowa najdłuższy ciąg samogłosek wspólny z jednym z 15 poprzednich słów,
uśredniony (metoda Raplyzera, Malmi i in. 2016). Liczy też przypadkowe zbieżności, więc ma sens tylko jako porównanie
raperów. W projekcie: mierzone (`rhyme_density`).

---

## 2. Środki dźwiękowe

Powtarzanie głosek w obrębie wersu lub kilku sąsiednich wersów, **niezależnie od rymu**.

| Środek | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **2.1 Aliteracja** | Ta sama głoska (w wymowie) **na początku** co najmniej dwóch blisko stojących słów. | „**m**ówił tak, **m**ówił: **m**ówisz, **m**asz” (Taco Hemingway), „**M**amy **m**iłość, **m**amy nas” (Białas) | liczone (`alliterations_100`); automat wymaga 3 kolejnych słów treściowych; poza profilami (zależy od utworu) |
| **2.2 Asonans** | Ta sama samogłoska akcentowana powtarza się w co najmniej trzech blisko stojących słowach. | „s**a**m, t**a**k, z**a**wsze n**a**raz” *(przykład ogólny)* | **wyłączone** (trafność 0/53: w polszczyźnie powtórzenie samogłoski zbyt często jest przypadkiem) |
| **2.3 Konsonans** | Te same spółgłoski po samogłosce akcentowanej powtarzają się w kilku blisko stojących słowach, przy różnych samogłoskach. | „ko**stk**a, chu**stk**a, pu**stk**a” *(przykład ogólny)* | **wyłączone** |
| **2.4 Onomatopeja** | Wyraz naśladujący dźwięk. | „bum”, „skrrt”, „wrum wrum” *(przykłady ogólne)* | **wyłączone** |
| **2.5 Paronomazja** | Blisko siebie słowa **podobnie brzmiące**, ale **niezwiązane znaczeniowo** (różne słowa, nie odmiany jednego słowa). | „Dają milion **czysto**, do ugrania milion **trzysta**” (Taco Hemingway), „na **ręce** … nie **ręczę**” (Eripe) | kandydaci (wektory brzmienia Parrisha) |

**Aliteracja a podobne głoski.** Według definicji aliteracja wymaga **tej samej** głoski. „**P**iękny **b**rzeg” to
nie aliteracja, tylko zbliżenie głosek. Macierz podobieństwa głosek nie może więc poszerzyć aliteracji o podobne
głoski; to byłaby inna figura.

---

## 3. Środki powtórzenia i składni

| Środek | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **3.1 Anafora** | Kolejne wersy **zaczynają się** tym samym słowem lub frazą. | „**Nie mam dziś czasu na** typów, co mają pretensje / **Nie mam dziś czasu na** myśli…” (Taco Hemingway) | liczone (`anaphoras_100`); poza profilami (zależy od utworu) |
| **3.2 Epifora** | Kolejne wersy **kończą się** tym samym słowem lub frazą. | „Oni piją se najdroższą łychę, **ale ja nie** / Po niej zdradzają swe tajemnice, **ale ja nie**” (Białas) | liczone (`epiphoras_100`); poza profilami |
| **3.3 Symploka** | Anafora i epifora naraz: kolejne wersy mają ten sam początek i ten sam koniec. | „**Mówię ci**, że to koniec **dziś** / **Mówię ci**, że to początek **dziś**” *(przykład ogólny)* | nie mierzone osobno (liczy się jako anafora i epifora) |
| **3.4 Anadiploza** | Koniec wersu powtarza się na początku następnego. | „Ale zagłuszają go ciągle jebane **problemy** / **Problemy**, problemy…” (Białas) | nie mierzone |
| **3.5 Epizeuksa** | To samo słowo powtórzone kilka razy z rzędu. | „**Jebać, jebać, jebać** wszystkie kurwy…” (Kaz Bałagane), „Hype, hype, hype…” (Quebonafide) | nie mierzone (celowo **nie** liczymy jej jako aliteracji ani powtórzenia frazy) |
| **3.6 Powtórzenie frazy** | Ciąg co najmniej dwóch różnych słów powtarza się w wersie albo wraca z poprzedniego wersu, poza jego początkiem i końcem (te są anaforą i epiforą). | „Spaceruję po mieście, **każdy wbija wzrok** / **Każdy wbija wzrok** we mnie…” (Białas) | mierzone (`phrase_repetitions_100`) |
| **3.7 Paralelizm składniowy** | Sąsiednie wersy mają tę samą budowę zdania: te same części mowy w tej samej kolejności. | „**Na koncertach mam wiele łap** / **Po koncertach mam wiele pań**” (Żabson) | **wyłączone** (trafność 8/18) |
| **3.8 Chiazm** | Dwa człony powtórzone w odwróconej kolejności (A B / B A). | „Nie żyję, by rapować, rapuję, by żyć” *(przykład ogólny)* | nie mierzone |
| **3.9 Figura etymologiczna** | Zestawienie słów o tym samym rdzeniu (np. rzeczownik i czasownik). | „Zostaję **tłumaczem**, **tłumaczę** tysiące CV” (Taco Hemingway) | nie mierzone osobno; ten przykład jest dziś wśród gier słów jako paronomazja, co według definicji 2.5 jest błędem klasyfikacji |
| **3.10 Refren (hook)** | Fragment powtarzany w utworze między zwrotkami. | | nie środek do liczenia: w statystykach refren liczy się **raz** |

---

## 4. Gry słów

**Gra słów (kalambur)** to nazwa zbiorcza: efekt powstaje z tego, że brzmienie lub forma słowa niesie dwa sensy
naraz. Podrodzaje:

| Środek | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **4.1 Dwuznaczność (polisemia)** | Jedno słowo w jednym miejscu działa w dwóch znaczeniach naraz. | „wszystko **wisi** mi jak Antygona” (Eripe): „nie obchodzi” i „wisi na pętli” | kandydaci (Słowosieć + adnotacje fanów) |
| **4.2 Homofonia** | Dwa różne słowa lub zwroty brzmią identycznie. | „**Lata miną** / **Lata z miną** pana świata” (Eripe) | kandydaci (słownik fonetyczny + adnotacje) |
| **4.3 Paronomazja** | zob. 2.5: słowa podobnie brzmiące, niezwiązane znaczeniowo | | kandydaci |
| **4.4 Pancz (punchline)** | Puenta wersu lub dwuwersu, zwykle oparta na grze słów albo zaskakującym porównaniu. W rapie to cel, a nie osobna figura: pancz *korzysta* z 4.1–4.3 i 5.1. | „siedzę **zawieszony** jak Cantona” (Eripe): porównanie + dwuznaczność | nie mierzone osobno |

Na stronie gry słów są tylko przykładami. Ich liczba zależy od aktywności fanów na Geniusie, więc nie trafia do
porównań.

---

## 5. Tropy i odniesienia

| Środek | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **5.1 Porównanie** | Zestawienie dwóch rzeczy za pomocą „jak”, „niczym”, „jakby”. W rapie często z nazwą własną. | „Kiwałem ją jak Mbappé” (Białas), „Wąsy jak Krzysiu Krawczyk” (Taco Hemingway) | liczone (`comparisons_100_lines`) |
| **5.2 Metafora** | Przeniesienie znaczenia bez „jak”: rzecz nazwana tak, jakby była czymś innym. | „Moje flow już nie zamiata, ono **goni Złoty Znicz**” (Quebonafide) | nie mierzone |
| **5.3 Metonimia** | Nazwanie rzeczy przez coś z nią związanego (marka zamiast przedmiotu, miejsce zamiast ludzi). | „mam na sobie całe Gucci” *(przykład ogólny)* | nie mierzone |
| **5.4 Hiperbola** | Celowe wyolbrzymienie. | „Mam w kieszeni cały świat” *(przykład ogólny)* | nie mierzone |
| **5.5 Ironia** | Powiedzenie czegoś, co znaczy odwrotnie. | | nie mierzone |
| **5.6 Antyteza** | Zestawienie przeciwieństw w sąsiednich członach. | „Choć masz to **czarno na białym**” (Eripe) | nie mierzone |
| **5.7 Oksymoron** | Połączenie słów o sprzecznych znaczeniach w jedno określenie. | „gorzki sukces” *(przykład ogólny)* | nie mierzone |
| **5.8 Aluzja (odniesienie)** | Nawiązanie do osoby, dzieła, wydarzenia lub innego rapera bez objaśniania go. | „Kiwałem ją jak Mbappé” (Białas), „jak mixu Deysa” (Eripe) | mierzone jako **odniesienia**: nazwy własne na 1000 słów (NER), bez oceny, czy to aluzja |

---

## 6. Budowa wersu i język

| Środek | Definicja | Przykład | W projekcie |
|---|---|---|---|
| **6.1 Przerzutnia** | Zdanie nie kończy się z końcem wersu i przechodzi do następnego. | „Wszystkim, którzy ciągle pozostają na dnie / Mówię adieu” (Taco Hemingway) | **wyłączone** (pokrycie 1/8; bez nagrania nie widać pauzy ani frazowania) |
| **6.2 Wtrącenie obcojęzyczne (makaronizm)** | Słowo lub fraza z innego języka w polskim tekście. | „Klimat cięższy od Titanica, **I'll be back**” (Quebonafide) | mierzone (`english_share`) |
| **6.3 Neologizm** | Słowo nowo utworzone przez autora. | „Internaziomal” (Żabson, tytuł płyty) | zbierane jako słowa spoza słowników (`out_of_dictionary_1000`), jeszcze nieoddzielone od slangu i literówek |
| **6.4 Ad-lib** | Wtrącony okrzyk lub dograny głos („ej”, „yeah”, „skrrt”), zwykle w nawiasie na Geniusie. | | usuwane przed analizą; liczone osobno (`adlibs_100_lines`) |

---

## 7. Rytm i flow (z nagrań)

Te środki istnieją tylko w wykonaniu, nie w tekście. Wymagają nagrań: oddzielenia wokalu, wyrównania sylab w czasie,
wykrycia bitu. Zob. [roadmap.md](roadmap.md).

| Środek | Definicja |
|---|---|
| **Flow** | Sposób rozłożenia sylab w czasie względem bitu: tempo, akcenty, pauzy. |
| **Synkopa** | Akcent sylaby padający między uderzeniami bitu zamiast na uderzenie. |
| **Double-time** | Nawijka dwa razy szybsza niż podstawowe tempo utworu. |
| **Triole** | Sylaby w grupach po trzy na jedno uderzenie. |
| **Pauza** | Celowa cisza w nawijce, często przed panczem. |

---

## 8. Nazwy w kodzie

| W kodzie / danych | W słowniku |
|---|---|
| `exact` | rym dokładny (1.1) |
| `assonance` | rym asonansowy (1.1) |
| `imperfect` | w modelu Hirjee i Browna: rym niedokładny inny niż asonansowy; linijka z reguł dzieli go na `consonance` i `approx` |
| `kind = end` / `internal` | rym końcowy / wewnętrzny (1.6) |
| `anchor = clausal` / `in_word` / `consonance` | rym klauzulowy / wewnątrzwyrazowy (1.5) / konsonansowy (1.1) |
| `rhyme_length`, `three_plus_share` | długość rymu, rym wielokrotny (1.4) |
| `rhyme_density` | gęstość rymów (1.11) |
| `alliteration` | aliteracja (2.1) |
| `assonance_chain` | asonans (2.2) |
| `consonance_chain` | konsonans (2.3) |
| `onomatopoeia` | onomatopeja (2.4) |
| `paronomasia.csv` | paronomazja (2.5) |
| `anaphora`, `epiphora` | anafora (3.1), epifora (3.2) |
| `phrase_repetition` | powtórzenie frazy (3.6) |
| `parallelism` | paralelizm składniowy (3.7) |
| `homophones.csv`, `polysemy.csv`, `wordplay_*.csv` | homofonia (4.2), dwuznaczność (4.1), gry słów (4) |
| `references_*` | aluzja / odniesienie (5.8) |
| `enjambment` | przerzutnia (6.1) |
| `english_share` | wtrącenie obcojęzyczne (6.2) |
