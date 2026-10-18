# Glossary of stylistic devices in rap

Every device has one definition here; the other documents, the pages and the code use these names. Polish terms
are given in brackets.

## Principles

1. **One definition per device.** The definition says what the device *is*, regardless of how it is measured.
2. **A measurement may be narrower than the definition, never different.** Example: alliteration needs at least two
   words by definition, but the detector starts at three, because two words with the same initial sound happen by
   chance. The detector catches part of the alliterations, but counts nothing that is not one.
3. **Sound, not spelling.** Sound devices are judged on pronunciation: „chata / hak” and „rzeka / żaba” start with
   the same sound (`x` and `ʐ`) despite different spelling.
4. **Examples** come from the corpus (rapper in brackets) unless marked *(general example)*.

Column **In the project**:
- **measured**: computed, validated and used in comparisons;
- **computed, not compared**: computed without a manual check or with an uncertain result;
- **off**: validation came out badly; still computed in the files but not shown;
- **candidates**: the detector proposes, a review decides; only examples are shown;
- **not measured**: outside the current scope.

---

## 1. Rhyme (rym)

A **rhyme** is a repeated sequence of sounds in two nearby places of a text, based mainly on vowels (or, in a
consonance rhyme, on consonants). The repeated sequence has the same number of syllables on both sides and counts in
pronunciation, not in spelling.

The sequence can sit anywhere in a line: at the end of a word, inside a word, across several words. The most common
case, known from poetry, is the **clausal rhyme** (rym klauzulowy): the sequence runs from the last stressed vowel of
a word to its end, and the sounds before that vowel do not count („**t**ango / **b**agno”). It is one value on axis
1.5, not a separate definition.

A rhyme is described on several independent axes, with one value on each, e.g. „end, clausal, feminine, assonant,
multisyllabic, poor, lexical”.

### 1.1 Axis: exactness

| Kind | Definition | Example | In the project (code) |
|---|---|---|---|
| **Exact rhyme** (rym dokładny) | All sounds of the repeated sequence are identical. | „czy już wize**runek** / niszczą nam opat**runek**” (Quebonafide) | measured (`exact`) |
| **Imperfect rhyme** (rym niedokładny) | The sounds agree only in part. Three subtypes below. | | |
| ↳ **assonant rhyme** | The vowels are identical, the consonants differ. | „taki mamy **lot** / twardo gramy **rok**” (Kaz Bałagane) | measured (`assonance`) |
| ↳ **consonance rhyme** (pararhyme) | The consonants are identical, the vowels differ. | „**las** / **los**” *(general example)* | **off** (not one true case among 100 candidates) |
| ↳ **approximate rhyme** | At least one vowel and one consonant differ, but the sounds are so close that the ear hears a rhyme. | „zamykają się **drzwi** / bo się bałem **żyć**” (Białas): `i`/`y` and a missing `ć` | `approx` in the ruler |

Note on naming: an **assonant rhyme** is a kind of rhyme. **Assonance** (2.2) is a separate figure, a vowel repeated
in several words; in the code it is `assonance_chain`.

### 1.2 Axis: stress position

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Masculine rhyme** | Stress on the last syllable; the rhyme starts in the last syllable. | „**lot** / **rok**” (Kaz Bałagane), „Jack / I'll be back” (Quebonafide) | not measured separately |
| **Feminine rhyme** | Stress on the penultimate syllable; the rhyme has two syllables. The basic kind in Polish. | „t**ango** / b**agno**” *(general example)* | not measured separately |
| **Dactylic rhyme** | Stress on the antepenultimate syllable; the rhyme has three syllables. | „**fi**zyka / **li**ryka” *(general example; here the norm puts the stress on the third syllable from the end)* | not measured separately |

### 1.3 Axis: agreement with stress

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Stress-aligned rhyme** | The stressed syllables of both sides face each other. | „t**a**ngo / b**a**gno” | ruler |
| **Shifted-stress rhyme** | The sequence matches only when one side is read with the stress somewhere other than the norm. The rapper bends pronunciation to make the rhyme. | „szybk**a** / koleg**a**” with the stress on the final „-ga” *(general example)* | **off** (candidates, often stress errors in the dictionary; only a recording can confirm them) |

### 1.4 Axis: length

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Rhyme length** | Number of syllables in the repeated sequence. | | measured (`rhyme_length`) |
| **Multisyllabic rhyme** (rym wielokrotny) | A rhyme of **at least 3 syllables**, longer than the basic feminine rhyme. | „postawy marzyc**ielskiej** / laurki od straży m**iejskiej**” (Taco Hemingway), „wlokę od st**artu** / ochotę do ż**artu**” (Oxon) | measured (`three_plus_share`) |

### 1.5 Axis: anchoring in the word

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Clausal rhyme** | The sequence ends at the end of a word on both sides and starts at the stressed vowel (or earlier, when it runs back across words). | „p**olskie tango** / gr**ząskie bagno**” | measured |
| **In-word rhyme** (rym wewnątrzwyrazowy) | The sequence starts or ends inside a word on at least one side. The multisyllabic rhyme „on the vowels” typical of rap, independent of word boundaries. | „**zakaza**ny owoc / **za kaza**nie to” *(general example)*: „a-ka-za” matches, the endings „-ny” and „-nie” do not | **off** (precision 46%) |

### 1.6 Axis: position in the line

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **End rhyme** | Both sides end at the end of a line. | „opat**runek** / wize**runek**” above | measured (up to 3 lines apart) |
| **Internal rhyme** | At least one side lies inside a line. | „**Ogromny** hol, w nim znajduję jakiś **skromny** fotel” (Taco Hemingway) | measured as the excess over chance (`internal_rhymes_excess`) |

### 1.7 Axis: richness

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Poor rhyme** | Agreement starts at the vowel. | „**t**ama / **br**ama” | computed |
| **Rich rhyme** | The consonant(s) right before the first vowel of the sequence agree too. | „b**rama** / **rama**”, „t**rawa** / sp**rawa**”: `r` before `a` in both | computed (`rich_share`) |

### 1.8 Axis: material

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Lexical rhyme** | Different stems rhyme, or the rhyme reaches beyond the inflectional ending. | „t**ango** / b**agno**” | computed |
| **Grammatical rhyme** | Words of the same part of speech rhyme only on a shared inflectional ending or suffix („-iłem”, „-ować”, „-ami”). Easy, considered weaker. | „zrob**iłem** / kup**iłem**” | computed (`grammatical_share`) |

### 1.9 Axis: construction

| Kind | Definition | Example | In the project |
|---|---|---|---|
| **Composite rhyme** (rym składany) | One side of the rhyme is several words, the other one word. | „**do mnie** / **skromnie**” *(general example)* | not measured separately (scored like any other rhyme) |
| **Homonymic rhyme** | Words with identical sound and different meanings rhyme. It is also wordplay. | „**może** / **morze**” *(general example)* | candidates (homophones, section 4) |
| **Tautological rhyme** | The same word or forms of one word rhyme with each other. | „...ziomal / ...ziomal” (Żabson), „mówić / mówisz” | **not counted as a rhyme**; a repeated word is an epiphora (3.2) |

### 1.10 Axis: scheme in a verse

| Kind | Definition | In the project |
|---|---|---|
| **Couplets** (aabb) | Consecutive pairs of lines rhyme. | computed on quatrains, not compared (`scheme_aabb`) |
| **Alternating** (abab) | Every other line rhymes. | computed, not compared (`scheme_abab`) |
| **Enclosed** (abba) | First with fourth, second with third. | computed, but at chance level (about 1%), so not shown |
| **Monorhyme** (aaaa…) | All lines of a verse on one rhyme. Common in rap. | computed on quatrains, not compared (`scheme_monorhyme`) |

Rhyme families over a whole verse (any scheme, e.g. ABABCDCD): `src/rapdna/experiments/families.py`, shown in the
local song browser (`rapdna browser`). Code: `src/rapdna/stats/schemes.py`. Quatrains are counted from the start of
a verse; in quatrains of random lines every scheme comes out below 1%.

### 1.11 Rhyme density

A **measure**, not a device. For every word, the longest vowel sequence shared with one of the 15 previous words,
averaged (the Raplyzer method, Malmi et al. 2016). It counts chance matches too, so it only makes sense as a
comparison between rappers. In the project: measured (`rhyme_density`).

---

## 2. Sound devices

Repetition of sounds within a line or a few neighbouring lines, **independent of rhyme**.

| Device | Definition | Example | In the project |
|---|---|---|---|
| **2.1 Alliteration** (aliteracja) | The same sound (in pronunciation) **at the start** of at least two nearby words. | „**m**ówił tak, **m**ówił: **m**ówisz, **m**asz” (Taco Hemingway), „**M**amy **m**iłość, **m**amy nas” (Białas) | computed (`alliterations_100`); the detector needs 3 consecutive content words; out of profiles (depends on the song) |
| **2.2 Assonance** (asonans) | The same stressed vowel repeats in at least three nearby words. | „s**a**m, t**a**k, z**a**wsze n**a**raz” *(general example)* | **off** (precision 0/53: in Polish a repeated vowel happens by chance too often) |
| **2.3 Consonance** (konsonans) | The same consonants after the stressed vowel repeat in several nearby words, with different vowels. | „ko**stk**a, chu**stk**a, pu**stk**a” *(general example)* | **off** |
| **2.4 Onomatopoeia** | A word imitating a sound. | „bum”, „skrrt”, „wrum wrum” *(general examples)* | **off** |
| **2.5 Paronomasia** (paronomazja) | Nearby words that **sound alike** but are **unrelated in meaning** (different words, not forms of one word). | „Dają milion **czysto**, do ugrania milion **trzysta**” (Taco Hemingway), „na **ręce** … nie **ręczę**” (Eripe) | candidates (Parrish sound vectors) |

**Alliteration and similar sounds.** By definition alliteration needs **the same** sound. „**P**iękny **b**rzeg” is
not alliteration but a sound approximation. A phoneme similarity matrix therefore cannot widen alliteration to similar sounds; that would be a different
figure.

---

## 3. Repetition and syntax

| Device | Definition | Example | In the project |
|---|---|---|---|
| **3.1 Anaphora** (anafora) | Consecutive lines **start** with the same word or phrase. | „**Nie mam dziś czasu na** typów, co mają pretensje / **Nie mam dziś czasu na** myśli…” (Taco Hemingway) | computed (`anaphoras_100`); out of profiles (depends on the song) |
| **3.2 Epiphora** (epifora) | Consecutive lines **end** with the same word or phrase. | „Oni piją se najdroższą łychę, **ale ja nie** / Po niej zdradzają swe tajemnice, **ale ja nie**” (Białas) | computed (`epiphoras_100`); out of profiles |
| **3.3 Symploce** | Anaphora and epiphora at once: consecutive lines share the start and the end. | „**Mówię ci**, że to koniec **dziś** / **Mówię ci**, że to początek **dziś**” *(general example)* | not measured separately (counts as anaphora and epiphora) |
| **3.4 Anadiplosis** | The end of a line repeats at the start of the next. | „Ale zagłuszają go ciągle jebane **problemy** / **Problemy**, problemy…” (Białas) | not measured |
| **3.5 Epizeuxis** | The same word repeated several times in a row. | „**Jebać, jebać, jebać** wszystkie kurwy…” (Kaz Bałagane), „Hype, hype, hype…” (Quebonafide) | not measured (deliberately **not** counted as alliteration or phrase repetition) |
| **3.6 Phrase repetition** | A run of at least two different words repeats in a line or comes back from the previous line, outside its start and end (those are anaphora and epiphora). | „Spaceruję po mieście, **każdy wbija wzrok** / **Każdy wbija wzrok** we mnie…” (Białas) | measured (`phrase_repetitions_100`) |
| **3.7 Syntactic parallelism** | Neighbouring lines have the same sentence structure: the same parts of speech in the same order. | „**Na koncertach mam wiele łap** / **Po koncertach mam wiele pań**” (Żabson) | **off** (precision 8/18) |
| **3.8 Chiasmus** | Two members repeated in reverse order (A B / B A). | „Nie żyję, by rapować, rapuję, by żyć” *(general example)* | not measured |
| **3.9 Figura etymologica** | Words with the same stem side by side (e.g. a noun and a verb). | „Zostaję **tłumaczem**, **tłumaczę** tysiące CV” (Taco Hemingway) | not measured separately; this example is currently among the wordplay as paronomasia, which by definition 2.5 is a misclassification |
| **3.10 Chorus (hook)** | A part repeated between the verses. | | not a device to count: a chorus counts **once** in the statistics |

---

## 4. Wordplay

**Wordplay** (gra słów, kalambur) is an umbrella name: the effect comes from a sound or form carrying two senses at
once. Subtypes:

| Device | Definition | Example | In the project |
|---|---|---|---|
| **4.1 Double meaning (polysemy)** | One word in one place works in two senses at once. | „wszystko **wisi** mi jak Antygona” (Eripe): „I don't care” and „hangs from a noose” | candidates (Słowosieć + fan annotations) |
| **4.2 Homophony** | Two different words or phrases sound identical. | „**Lata miną** / **Lata z miną** pana świata” (Eripe) | candidates (phonetic dictionary + annotations) |
| **4.3 Paronomasia** | see 2.5: similar-sounding words, unrelated in meaning | | candidates |
| **4.4 Punchline** (pancz) | The point of a line or couplet, usually built on wordplay or a surprising comparison. In rap it is a goal, not a separate figure: a punchline *uses* 4.1–4.3 and 5.1. | „siedzę **zawieszony** jak Cantona” (Eripe): comparison + double meaning | not measured separately |

On the site wordplay appears only as examples. How much of it is found depends on how active a rapper's fans are on
Genius, so it is not compared.

---

## 5. Tropes and references

| Device | Definition | Example | In the project |
|---|---|---|---|
| **5.1 Simile** (porównanie) | Two things compared with „jak”, „niczym”, „jakby”. In rap often with a proper name. | „Kiwałem ją jak Mbappé” (Białas), „Wąsy jak Krzysiu Krawczyk” (Taco Hemingway) | computed (`comparisons_100_lines`) |
| **5.2 Metaphor** | Meaning carried over without „jak”: a thing named as if it were something else. | „Moje flow już nie zamiata, ono **goni Złoty Znicz**” (Quebonafide) | not measured |
| **5.3 Metonymy** | A thing named by something associated with it (a brand for the object, a place for the people). | „mam na sobie całe Gucci” *(general example)* | not measured |
| **5.4 Hyperbole** | Deliberate exaggeration. | „Mam w kieszeni cały świat” *(general example)* | not measured |
| **5.5 Irony** | Saying something that means the opposite. | | not measured |
| **5.6 Antithesis** | Opposites side by side in neighbouring members. | „Choć masz to **czarno na białym**” (Eripe) | not measured |
| **5.7 Oxymoron** | Words with contradictory meanings joined into one phrase. | „gorzki sukces” *(general example)* | not measured |
| **5.8 Allusion (reference)** | A reference to a person, work, event or another rapper without explaining it. | „Kiwałem ją jak Mbappé” (Białas), „jak mixu Deysa” (Eripe) | measured as **references**: proper names per 1000 words (NER), without judging whether it is an allusion |

---

## 6. Line structure and language

| Device | Definition | Example | In the project |
|---|---|---|---|
| **6.1 Enjambment** (przerzutnia) | A sentence does not end with the line and runs into the next one. | „Wszystkim, którzy ciągle pozostają na dnie / Mówię adieu” (Taco Hemingway) | **off** (recall 1/8; without a recording neither the pause nor the phrasing is visible) |
| **6.2 Foreign-language insertion** (makaronizm) | A word or phrase from another language in a Polish text. | „Klimat cięższy od Titanica, **I'll be back**” (Quebonafide) | measured (`english_share`) |
| **6.3 Neologism** | A word newly made up by the author. | „Internaziomal” (Żabson, album title) | collected as out-of-dictionary words (`out_of_dictionary_1000`), not yet separated from slang and typos |
| **6.4 Ad-lib** | An interjected shout or backing voice („ej”, „yeah”, „skrrt”), usually in brackets on Genius. | | removed before the analysis; counted separately (`adlibs_100_lines`) |

---

## 7. Rhythm and flow (from recordings)

These exist only in the performance, not in the text. They need recordings: vocal separation, syllables aligned in
time, beat detection. See [roadmap.md](roadmap.md).

| Device | Definition |
|---|---|
| **Flow** | How syllables are laid out in time against the beat: tempo, stresses, pauses. |
| **Syncopation** | A syllable stress falling between beats instead of on them. |
| **Double-time** | Delivery twice as fast as the basic tempo of the song. |
| **Triplet flow** | Syllables in groups of three per beat. |
| **Pause** | A deliberate silence in the delivery, often before a punchline. |

---

## 8. Names in the code

| In the code / data | In this glossary |
|---|---|
| `exact` | exact rhyme (1.1) |
| `assonance` | assonant rhyme (1.1) |
| `imperfect` | in the Hirjee & Brown baseline: an imperfect rhyme other than assonant; the ruler splits it into `consonance` and `approx` |
| `kind = end` / `internal` | end / internal rhyme (1.6) |
| `anchor = clausal` / `in_word` / `consonance` | clausal / in-word (1.5) / consonance rhyme (1.1) |
| `rhyme_length`, `three_plus_share` | rhyme length, multisyllabic rhyme (1.4) |
| `rhyme_density` | rhyme density (1.11) |
| `alliteration` | alliteration (2.1) |
| `assonance_chain` | assonance (2.2) |
| `consonance_chain` | consonance (2.3) |
| `onomatopoeia` | onomatopoeia (2.4) |
| `paronomasia.csv` | paronomasia (2.5) |
| `anaphora`, `epiphora` | anaphora (3.1), epiphora (3.2) |
| `phrase_repetition` | phrase repetition (3.6) |
| `parallelism` | syntactic parallelism (3.7) |
| `homophones.csv`, `polysemy.csv`, `wordplay_*.csv` | homophony (4.2), double meaning (4.1), wordplay (4) |
| `references_*` | allusion / reference (5.8) |
| `enjambment` | enjambment (6.1) |
| `english_share` | foreign-language insertion (6.2) |
