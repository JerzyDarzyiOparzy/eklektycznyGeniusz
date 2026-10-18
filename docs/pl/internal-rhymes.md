# Rymy wewnętrzne

Rymy końcowe są rozwiązane (trafność 97,8%, pokrycie 96,4%). Otwartym problemem są rymy w środku wersu: polszczyzna
ma sześć samogłosek i wiele jednakowych końcówek odmiany, więc dwa podobnie brzmiące słowa są w prawie każdej parze
wersów. Sam tekst rzadko mówi, które z nich raper zrobił celowo.

Ta strona porównuje wypróbowane metody. Kod jest w `src/rapdna/experiments/`, a porównanie uruchamia
`rapdna compare-rhymes` na oznaczeniach wzorcowych (16 utworów, 724 wersy, zob. [validation.md](validation.md)).

## Miary

Każda sylaba jest zaznaczona albo nie. Trafność to udział sylab zaznaczonych przez metodę, które są zaznaczone we
wzorcu; pokrycie to udział sylab wzorca, które metoda zaznaczyła. Stałe dobierano na połowie utworów, a wyniki podajemy
na drugiej połowie (test).

## Porównanie

| Metoda | Pomysł | Sylaby T / P / F1 (test) | Zostaje |
|---|---|---|---|
| Linijka z reguł | podobieństwo brzmienia końcówek słów w dowolnym miejscu dwóch wersów | sama liczba na poziomie przypadku | tylko jako liczba ponad przypadek |
| Wspólne łańcuchy samogłosek | dowolny łańcuch samogłosek wspólny dla sąsiednich wersów | 2–3 samogłoski: brak nadwyżki nad przypadkiem | nie |
| Echo rymu końcowego | układ samogłosek rymu końcowego powtórzony w środku bliskich wersów | ok. 42% zamierzonych | nie |
| Macierz sylab | powtórzone pasy samogłosek oceniane zaskoczeniem względem przypadku | trafność 6–24% | nie |
| Uczone oceny klocków | oceny całych klocków rymowych uczone na korpusie | gorsze od reguł na rymach końcowych | nie |
| Stopy | ten sam klucz samogłosek w komórkach-stopach w pobliżu | 48 / 95 / 63,9 | nie: zaznacza dwa razy więcej niż ludzie |
| Szansa rymu | model logistyczny na jawnych wskazówkach, dopasowany do wzorca | 74 / 82 / 77,7 (odłóż-utwór 75,7 łącznie) | do porównań |
| **Pary wersów** | sąsiednie wersy rymowane pozycja po pozycji, plus motywy | **79 / 78 / 78,3** | najlepsza dotąd |

## Co pokazuje wzorzec

- 96% zaznaczonych fragmentów rymuje się z wersem tuż obok.
- Jedna grupa rymu odpowiada jednemu ciągowi samogłosek w zwrotce w 82–85% przypadków: ludzie zaznaczają asonanse,
  ale wybierają je według miejsca w wersie, równoległości i ciągów sylab.
- Dwie ostatnie sylaby wersu są zaznaczone w 91–95% przypadków; w środku wersu tylko 23% sylab.
- Wybór rymów wewnętrznych z samego tekstu ma sufit około 60% trafności, tyle, ile Hirjee i Brown podają wobec ręcznych
  oznaczeń.

## Metody

**Stopy.** Wers dzielimy na komórki-stopy: sylaba akcentowana z resztą słowa, krótkie słowo złączone z następnym,
reszta dłuższego słowa. Komórka jest zaznaczona, gdy jej klucz samogłosek powtarza się w pobliżu. Metoda znajduje
prawie każdy rym zaznaczony przez ludzi, ale zaznacza mniej więcej dwa razy więcej.

**Szansa rymu.** Te same komórki z jawnymi cechami: odległość od końca wersu, równoległy partner w następnym wersie,
echo rymu końcowego, ciąg komórek, słowa funkcyjne, zgodność spółgłosek. Regresja logistyczna uczy się tylko wag tych
wskazówek, na oznaczeniach wzorcowych, nigdy na korpusie. Najsilniejsze wskazówki: rym końcowy +1,7, odległość co
najmniej 4 sylab od końca −2,5, słowa funkcyjne −0,9, równoległy partner +0,9, ciąg komórek +0,7.

**Pary wersów.** We wzorcu sąsiednie wersy rymują się pozycja po pozycji: „**Chudy** jak Mike **Skinner** **daję**
**tłuszcz na** **podkład**” / „**Wczuty** jak w ro**dzinę** **chwalę** **brud jak** **Bonhart**”. Reguła bierze
najdłuższy ciąg komórek o tych samych kluczach samogłosek, w tej samej kolejności i podobnym miejscu w dwóch
sąsiednich wersach (co najmniej 3 sylaby), i dokłada komórki dwusylabowe, których klucz jest już zaznaczony w wersie
obok (motywy ciągnięte przez kilka wersów, po jednym słowie).

**Nagrania.** Na wyrównanych nagraniach rymy końcowe padają na pozycje 11–15 taktu (koło 4. bitu, jak w literaturze).
Dla rymów wewnętrznych pozycja w takcie dodaje niewiele (+0,3 F1), bo w tych utworach wers to mniej więcej takt, więc
miejsce w wersie niesie tę samą informację.

## Całe zwrotki

Zamiast pojedynczych rymów można ocenić, jak gęsto zrymowana jest zwrotka: udział zaznaczonych sylab i liczba
zaznaczonych sylab na parę wersów. Korelacja rang ze wzorcem na 34 sekcjach wynosi 0,5–0,6: umiarkowana i niestabilna
przy tej liczbie zwrotek.

## Dalej

- Więcej oznaczeń wzorcowych, żeby dobierać stałe bez ponownego użycia utworów testowych.
- Nagrania całego korpusu, dla utworów, w których wersy nie pokrywają się z taktami.
- Zmierzona zgodność dwóch osób oznaczających te same zwrotki: sufit dla każdej metody.
