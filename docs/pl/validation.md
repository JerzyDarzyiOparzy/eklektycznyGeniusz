# Walidacja

## Wzorce

| Wzorzec | Rozmiar | Do czego |
|---|---|---|
| Złoty zbiór | 300 par rymów losowanych z całej skali ocen, 500 losowych wersów | progi rymów, figury |
| Złoty zbiór R | 300 kandydatów linijki z reguł, po 100 na rodzaj rymu, z całej skali ocen | progi linijki, rodzaj rymu |
| Oznaczenia rymów | 16 utworów, 724 wersy, 1 988 zaznaczonych fragmentów pogrupowanych w rymy, z publicznie dostępnych analiz rymów | rymy końcowe, rymy wewnętrzne |
| Próbki | 40–100 losowych trafień na cechę | odniesienia, perspektywa, porównania, słowa angielskie, wulgaryzmy |
| Odsłuch | nagrania 20 utworów | czas słów, bity, wymowa |

Złote zbiory oznaczał na ślepo (bez wyniku metody) model językowy, a autor sprawdzał je na próbkach. Progi wybieramy
na nich w walidacji krzyżowej, więc podane wyniki nie są dopasowane do tych samych danych. Oznaczenia rymów zrobili
ludzie, niezależnie od projektu.

## Wyniki

| Cecha | Wzorzec | Wynik | W porównaniach |
|---|---|---|---|
| Rymy końcowe | oznaczenia rymów, ostatnia sylaba wersu | trafność 97,8%, pokrycie 96,4% | tak |
| Rodzaj rymu (dokładny / asonansowy) | złoty zbiór R | zgodność 86% | tak |
| Rymy wewnętrzne, surowa liczba | losowe wersy z innych utworów | 61% liczby z sąsiednich wersów | nie |
| Rymy wewnętrzne ponad przypadek | wbudowana kontrola przypadku | trafność samych rymów 77% | tak |
| Rymy wewnątrzwyrazowe | złoty zbiór R | trafność 40% | nie |
| Rymy konsonansowe | złoty zbiór R | ani jednego prawdziwego na 100 kandydatów | nie |
| Anafory | złoty zbiór | trafność 89%, pokrycie 67% | liczone, poza profilami |
| Epifory | złoty zbiór | trafność 92%, pokrycie 92% | liczone, poza profilami |
| Powtórzenia fraz | złoty zbiór | trafność 18/18, pokrycie 86% | tak |
| Aliteracje | złoty zbiór | trafność 5/7 (mała próba) | liczone, poza profilami |
| Paralelizmy | złoty zbiór | trafność 44%, pokrycie 44% | nie |
| Przerzutnie | złoty zbiór | pokrycie 1/8 | nie |
| Łańcuchy asonansów | złoty zbiór | 0/53 | nie |
| Sylaby na wers | ręczne liczenie | 24/24 wersy | tak |
| Słowa angielskie | próbka | trafność 40/40 | tak |
| Porównania | próbka | 34/40 | tak |
| Perspektywa | próbka | 37/40 | tak |
| Odniesienia | próbka | trafność 87% | tak |
| Tematy | próbka | 72% fragmentów pasuje do nazwy tematu; 56% fragmentów bez tematu | ostrożnie |

## Kontrola przypadku

| Miara | Losowe / sąsiednie wersy |
|---|---|
| Rymy końcowe | 0,04–0,13 |
| Rymy wewnętrzne (surowe) | 0,61 |
| Rymy wewnątrzwyrazowe | 0,64 |
| AABB, ABAB, monorym | poniżej 1% losowych czwórek |

Cechy, której poziom przypadkowy jest bliski prawdziwemu, nie używamy, nawet jeśli jej przykłady wyglądają
przekonująco.
