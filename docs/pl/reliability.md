# Raper czy utwór? Rzetelność i profile

## Pytanie

Statystyka opisuje rapera tylko wtedy, gdy jego utwory są do siebie bardziej podobne niż do utworów innych raperów.
Badania rapu anglojęzycznego (MCFlow; Condit-Schultz, Ohriner) pokazały, że utwory jednego rapera często różnią się
bardziej niż raperzy między sobą. Sprawdzamy to samo.

## Metoda

Każdą cechę liczymy osobno dla każdego utworu z co najmniej 24 wersami rapera: 1 019 utworów, 20 raperów, mediana
44 utworów na rapera (`stats/reliability.py`).

- **ICC**: jaka część różnic między utworami wynika z tego, kto rapuje (1 = tylko raper, 0 = tylko utwór); model
  jednoczynnikowy losowy dla nierównych grup, przedział 95% z pomijania po jednym raperze.
- **eta²**: jaką część zmienności wyjaśnia raper, a jaką dekada wydania.
- **Utworów potrzeba**: ile utworów potrzeba, żeby średnia rapera osiągnęła rzetelność 0,8 (Spearman–Brown).
- **Rzetelność przy 44 utworach**: rzetelność średniej przy medianie wielkości dorobku.

## Wyniki

| Cecha | ICC (95%) | eta² raper / dekada | Utworów na 0,8 | Rzetelność przy 44 utworach |
|---|---|---|---|---|
| Długość rymu | 0,57 (0,16–0,98)¹ | 0,57 / 0,11 | 3 | 0,98 |
| Rymy ≥ 3 sylaby | 0,52 (0,21–0,84)¹ | 0,52 / 0,12 | 4 | 0,98 |
| Udział refrenu | 0,33 (0,21–0,46) | 0,33 / 0,17 | 8 | 0,96 |
| Sylaby na wers | 0,31 (0,14–0,48) | 0,31 / 0,04 | 9 | 0,95 |
| Wersy zrymowane | 0,29 (0,13–0,46) | 0,30 / 0,10 | 10 | 0,95 |
| Rymy dokładne | 0,29 (0,12–0,46) | 0,29 / 0,21 | 10 | 0,95 |
| Gęstość rymów | 0,27 (0,08–0,47) | 0,28 / 0,04 | 11 | 0,94 |
| Różnorodność słów (MATTR) | 0,23 (0,11–0,36) | 0,24 / 0,08 | 13 | 0,93 |
| Ad-liby | 0,20 (0,11–0,30) | 0,21 / 0,09 | 16 | 0,92 |
| Długość słów | 0,20 (0,03–0,36) | 0,20 / 0,00 | 16 | 0,92 |
| Wulgaryzmy | 0,20 (0,06–0,33) | 0,20 / 0,03 | 16 | 0,92 |
| Wersy na zwrotkę | 0,19 (0,09–0,30) | 0,20 / 0,06 | 17 | 0,91 |
| Powtarzalność | 0,17 (0,09–0,26) | 0,18 / 0,08 | 19 | 0,90 |
| Porównania | 0,14 (0,05–0,23) | 0,15 / 0,03 | 25 | 0,88 |
| Powtórzenia fraz | 0,13 (0,07–0,18) | 0,14 / 0,07 | 28 | 0,86 |
| Słowa rzadkie | 0,12 (0,00–0,23) | 0,13 / 0,02 | 30 | 0,86 |
| Słowa angielskie | 0,11 (0,03–0,19) | 0,12 / 0,07 | 32 | 0,84 |
| Tryb rozkazujący | 0,08 | 0,10 / 0,03 | 44 | 0,80 |
| Czas przeszły | 0,08 | 0,09 / 0,05 | 46 | 0,79 |
| Epifory | 0,07 | 0,08 / 0,01 | 56 | 0,76 |
| Slang | 0,06 | 0,08 / 0,00 | 59 | 0,75 |
| Własna ksywa | 0,05 | 0,06 / 0,05 | 78 | 0,69 |
| Anafory | 0,02 | 0,04 / 0,02 | 177 | 0,50 |
| Aliteracje | 0,01 | 0,03 / 0,01 | 350 | 0,33 |

¹ Wynik ciągnie jeden raper z bardzo długimi rymami (średnio 4,25 sylaby); bez tego rapera ICC wynosi około 0,36.

## Wnioski

1. Dla **każdej** cechy utwory jednego rapera różnią się bardziej niż raperzy (ICC poniżej 0,6). Styl to cecha
   dorobku, nie pojedynczej zwrotki.
2. Średnia z całego dorobku jest mimo to rzetelna: przy 44 utworach większość cech osiąga 0,8 lub więcej.
3. Anafory, aliteracje, epifory, własna ksywa i slang zależą głównie od utworu. Zostają w statystykach, ale nie
   trafiają do profili.
4. Porównania płyt (około 10 utworów) są wiarygodne tylko dla cech z ICC od około 0,28 w górę.
5. Dekada wyjaśnia mało (eta² ≤ 0,12), poza udziałem rymów dokładnych (0,21).
6. Utwór ma około 40 wersów, więc część różnic między utworami to szum pomiaru; ICC jest dolną granicą.

## Profile

Profil wymienia cechy, którymi raper się wyróżnia (`stats/profile.py`, `config/profile.yaml`):

1. Wartość rapera to średnia z jego utworów ważona liczbą słów.
2. Odporny z-score względem pozostałych raperów: (wartość − mediana) / (1,4826 · MAD).
3. Przedział 95% z losowania utworów rapera ze zwracaniem (bootstrap, 1 000 losowań).
4. Rzetelność średniej z ICC i liczby utworów rapera.

Cecha zostaje **wyróżnikiem**, gdy |z| ≥ 1, przedział nie przecina mediany korpusu, a rzetelność wynosi co najmniej
0,8. Profil pokazuje najwyżej dwa wyróżniki na wymiar stylu i pięć łącznie, żeby jeden wymiar (np. rymy) nie wypełnił
go w całości.
