# Plan rozwoju

## Nagrania

Tekst nic nie mówi o rytmie, a według literatury muzykologicznej to w rytmie style różnią się najbardziej. Działający
potok audio już jest (`rapdna audio <song_id>`, `src/rapdna/audio/`):

1. pobranie wersji z płyty z YouTube (yt-dlp);
2. oddzielenie wokalu (Demucs);
3. wyrównanie znanego tekstu do wokalu (wyrównanie wymuszone MMS z torchaudio), co daje czas każdego słowa i sylaby;
4. wykrycie bitów i taktów (beat_this), co daje pozycję każdej sylaby w takcie.

Na 20 utworach czas słów i bity potwierdził odsłuch, a pewność wyrównania zwrotek wynosi 0,64–0,91. Nagranie potrafi
też wybrać między polskim i angielskim odczytem słowa, ale raperzy często mówią trzecią, mieszaną wersję, więc takie
decyzje są tylko kandydatami do odsłuchu.

Kolejne kroki wymagają nagrań całego korpusu (około 13 godzin liczenia, około 0,2 MB wyników na utwór, jeśli
zostawiamy tylko wyniki i skompresowany wokal):

- sylaby na sekundę i na bit, double-time i triole;
- akcenty na bicie i poza nim, położenie rymów w takcie;
- zmiany flow w zwrotce, frazy a takty, pauzy;
- melodyjność (wysokość głosu), później mikrotiming.

## Większy korpus

60–100 raperów ze wszystkimi płytami studyjnymi, dobranych według tych samych kryteriów, z równowagą dekad: lista
„Antologii Polskiego Rapu” na Geniusie plus najczęściej oglądani raperzy z każdej dekady. Nagrania dla próbki.

## Badania do powtórzenia na polskim rapie

| Twierdzenie z rapu anglojęzycznego | Jak to sprawdzić |
|---|---|
| Utwory różnią się bardziej niż raperzy (MCFlow) | zrobione dla 20 raperów ([reliability.md](reliability.md)); powtórzyć na większym korpusie |
| Gęstość rymów rosła do około 2002 roku, potem lekko spadła; tempo malało | statystyki rymów i tempo według roku wydania |
| Rymy końcowe skupiają się koło 4. bitu | pozycje rymów w takcie (widoczne już na 20 utworach) |
| Około 4,5 sylaby na sekundę; double-time i triole jako typy flow | tempo sylab i dopasowanie do siatki |
| Na mocnych bitach częściej stoją samogłoski „jasne” (i, e) (Ammirante i Copelli) | samogłoska × pozycja w takcie |
| Raperzy w jednym utworze dopasowują flow do siebie (Komaniecki) | podobieństwo rytmu zwrotek w utworach z gośćmi |

## Język

- **Kategorie słów.** 2 734 formy spoza słowników do podziału na słowotwórstwo, slang, zapożyczenia i literówki
  oraz 4 443 nazwy własne do opisania (miasto, marka, raper…) z poprawioną wymową. Etykiety z modelu językowego,
  który dobrze zna polski, sprawdzone na próbce.
- **Modele wymowy.** Model „tekst → IPA” dostrojony na słowniku fonetycznym i poprawkach wymowy oraz model
  „nagranie → IPA” dostrojony na wyrównanych wokalach rapowych; razem mogłyby wybierać mieszane odczyty, których nie
  łapią reguły.
- **Tryb wypowiedzi** (opowieść, przechwałka, introspekcja, komentarz) na zwrotkę.

## Profile

- Profile dla każdej płyty, żeby odróżnić stały wyróżnik od zmiany stylu.
- Równe wagi wymiarów stylu w podobieństwie raperów i na mapie sceny.
