"""Scoring rhyme-marking methods against the reference rhyme annotations (`annotations.py`).

Unit: a song section (verse, chorus). A section is scored when at least MIN_MARKED of its lines carry a mark.
Measures:
- syllables: precision = share of syllables marked by the method that are marked in the reference; recall = share
  of reference syllables the method marked; separately for the line end (last 2 syllables) and the inside of a line;
- words: the same for words (a word is marked when at least one of its syllables is);
- pairs: pairs of words in the same group: precision and recall of pairs among words marked on both sides.
A marked word fragment („dłuża” in „wydłuża”) is converted to syllables by the vowels in the spelling (an i before a
vowel only softens, it is not a syllable).

Usage: python -m rapdna.validate.rhyme_eval → scores of feet.py and line_pairs.py, and a local comparison page
"""
import re
from collections import defaultdict

import pandas as pd

from rapdna import paths
from rapdna.rhymes.match import build_line
from rapdna.text.phonetics import Lexicon, WORD_RE, context_english, is_english_line, number_to_words, \
    polish_in_english_line, spelled_acronym
from rapdna.validate.annotations import DIR, load

WORDS = DIR / "words.parquet"
MIN_MARKED = 0.3
_V = re.compile(r"i(?=[aąeęoóuy])|([aąeęioóuy])", re.I)


def tokens_with_spans(text: str) -> list[tuple[str, int, int]]:
    out = []
    adlibs = [a.span() for a in re.finditer(r"\([^)]*\)", text)]  # ad-libs in brackets are skipped, as in the pipeline
    for m in WORD_RE.finditer(text):
        if any(a <= m.start() < b for a, b in adlibs):
            continue
        tok = m.group(0)
        for t in (number_to_words(tok).split() if tok.isdigit() else [tok]):
            out.append((t, m.start(), m.end()))
    return out


def words_for_rows(data: dict) -> pd.DataFrame:
    """Word pronunciation as in the pipeline (`pipeline.process`): dictionary, word-language rules, English lines."""
    rows = [(t, ri, r["text"]) for t, d in data.items() for ri, r in enumerate(d["rows"])]
    toks = {(t, ri): tokens_with_spans(text) for t, ri, text in rows}
    lex = Lexicon()
    lex.load({w for ts in toks.values() for w, _, _ in ts})
    eng = {k for k, ts in toks.items() if is_english_line([w for w, _, _ in ts])}
    ctx = set()
    for k, ts in toks.items():
        if k in eng:
            continue
        forms = [w for w, _, _ in ts]
        base = [lex.lang.get(w.lower()) == "en" for w in forms]
        ctx |= {(k, i) for i, (b, c) in enumerate(zip(base, context_english(forms, base))) if c and not b}
    lex.load_english({w for k in eng for w, _, _ in toks[k]} | {toks[k][i][0] for k, i in ctx})
    out = []
    for k, ts in toks.items():
        for wi, (w, a, b) in enumerate(ts):
            english = k in eng and not polish_in_english_line(w) or (k, wi) in ctx
            out.append({"title": k[0], "row": k[1], "w": wi, "form": w, "a": a, "b": b,
                        "ipa": spelled_acronym(w) or (lex.ipa_en[w.lower()] if english else lex[w]),
                        "lang": "en" if english else "pl"})
    df = pd.DataFrame(out)
    df.to_parquet(WORDS, index=False)
    return df


def vowel_positions(word: str) -> list[int]:
    """Positions of the vowel letters that form syllables (an i before a vowel is skipped)."""
    return [m.start(1) for m in _V.finditer(word) if m.group(1)]


def gold_syllables(line, words: pd.DataFrame, marks: list[dict]) -> dict[int, str]:
    """Syllable (unit) of the line → reference group."""
    by_word = defaultdict(list)
    for k, kl in enumerate(line.ks):
        by_word[kl.word].append(k)
    out = {}
    for m in marks:
        for w in words.itertuples():
            if w.b <= m["i"] or w.a >= m["j"] or w.w not in by_word:
                continue
            ks = by_word[w.w]
            if w.a >= m["i"] and w.b <= m["j"]:
                sel = ks
            else:
                vp = vowel_positions(w.form)
                inside = [n for n, p in enumerate(vp) if m["i"] <= w.a + p < m["j"]]
                if not vp or len(vp) != len(ks):  # spelling and pronunciation differ in syllables: letter ratio
                    lo = (max(m["i"], w.a) - w.a) / max(len(w.form), 1)
                    hi = (min(m["j"], w.b) - w.a) / max(len(w.form), 1)
                    inside = [n for n in range(len(ks)) if lo <= (n + 0.5) / len(ks) <= hi]
                sel = [ks[n] for n in inside if n < len(ks)]
            for k in sel:
                out[k] = m["group"]
    return out


def load_marks() -> tuple[dict, pd.DataFrame]:
    data = load()
    return data, pd.read_parquet(WORDS) if WORDS.exists() else words_for_rows(data)


def sections(data: dict | None = None, words: pd.DataFrame | None = None):
    """Scored sections: (song, song_id, section, line indices, words of the lines, Line objects, marks per line)."""
    if data is None:
        data, words = load_marks()
    for title, d in data.items():
        wt = words[words.title == title]
        mb = defaultdict(list)
        for m in d["marks"]:
            mb[m["row"]].append(m)
        secs = defaultdict(list)
        for ri, r in enumerate(d["rows"]):
            secs[r["section"]].append(ri)
        for sec, ris in secs.items():
            if sum(bool(mb[ri]) for ri in ris) < MIN_MARKED * len(ris) or len(ris) < 4:
                continue
            ws = [wt[wt.row == ri].sort_values("w").reset_index(drop=True) for ri in ris]
            lines = [build_line([(f, ipa, f, "X") for f, ipa in zip(w.form, w.ipa)]) for w in ws]
            yield title, d["song_id"], sec, ris, ws, lines, [mb[ri] for ri in ris]


def gold_sections(meter: bool = False) -> list[dict]:
    """Scored sections with their gold syllables; with meter=True only songs with an aligned recording, plus the bar
    position of every syllable."""
    from rapdna.validate.recordings import meter_for_rows

    out = []
    for title, sid, _, _, ws, lines, marks in sections():
        m = meter_for_rows(sid, ws, lines) if meter else None
        if meter and m is None:
            continue
        gold = {(li, k): g for li in range(len(lines)) for k, g in gold_syllables(lines[li], ws[li], marks[li]).items()}
        out.append({"title": title, "lines": lines, "meter": m, "gold": gold})
    return out


def pairs(groups: dict) -> set:
    by = defaultdict(set)
    for unit, g in groups.items():
        by[g].add(unit)
    return {(a, b) for us in by.values() for a in us for b in us if a < b}


def score(secs: list[dict], marked: list[list]) -> dict:
    """marked[i] = [(cell, group)] for section i. Syllables (all / line end / inside), words and pairs, in percent."""
    t = defaultdict(int)
    for s, mk in zip(secs, marked):
        auto = {(c.line, k): gid for c, gid in mk for k in range(c.start, c.end)}
        gold, lines = s["gold"], s["lines"]
        end = {(li, k) for li, line in enumerate(lines) for k in range(max(0, len(line.ks) - 2), len(line.ks))}
        A, G = set(auto), set(gold)
        for part, sel in (("syllables", lambda x: x), ("end", lambda x: x & end), ("internal", lambda x: x - end)):
            t[part, "tp"] += len(sel(A & G))
            t[part, "auto"] += len(sel(A))
            t[part, "gold"] += len(sel(G))

        def word_of(u):
            return u[0], lines[u[0]].ks[u[1]].word

        aw, gw = {word_of(u): g for u, g in auto.items()}, {word_of(u): g for u, g in gold.items()}
        both = set(aw) & set(gw)
        pa, pg = pairs({u: aw[u] for u in both}), pairs({u: gw[u] for u in both})
        for part, a, g in (("words", set(aw), set(gw)), ("pairs", pa, pg)):
            t[part, "tp"] += len(a & g)
            t[part, "auto"] += len(a)
            t[part, "gold"] += len(g)

    def pct(a, b):
        return round(100 * a / b, 1) if b else 0.0

    r = {}
    for part in ("syllables", "end", "internal", "words", "pairs"):
        r[f"{part}_P"] = pct(t[part, "tp"], t[part, "auto"])
        r[f"{part}_R"] = pct(t[part, "tp"], t[part, "gold"])
    r["syllables_F1"] = round(2 * r["syllables_P"] * r["syllables_R"] / max(r["syllables_P"] + r["syllables_R"], 1e-9), 1)
    return r


PALETTE = ["#fefe02", "#02fefe", "#fe6e6e", "#729ece", "#7efe02", "#feb66e", "#be829e", "#b2b2b2", "#02fe7e",
           "#fe02fe", "#d6ea6e", "#76be62", "#caca02", "#fe8202"]


def syllable_chars(form: str, n: int) -> list[tuple[int, int]]:
    """Approximate boundaries of n syllables in the spelling (cut before the consonant preceding a vowel)."""
    vp = vowel_positions(form)
    if len(vp) != n or n == 0:
        step = len(form) / max(n, 1)
        return [(round(i * step), round((i + 1) * step)) for i in range(n)]
    cuts = [0] + [max(vp[i - 1] + 1, vp[i] - 1) for i in range(1, n)] + [len(form)]
    return [(cuts[i], cuts[i + 1]) for i in range(n)]


def _paint(text: str, spans: list[tuple[int, int, str]]) -> str:
    from html import escape

    color = [None] * len(text)
    for a, b, c in spans:
        for x in range(max(a, 0), min(b, len(text))):
            color[x] = c
    out, x = [], 0
    while x < len(text):
        y = x
        while y < len(text) and color[y] == color[x]:
            y += 1
        seg = escape(text[x:y])
        out.append(f'<span style="background:{color[x]}">{seg}</span>' if color[x] else seg)
        x = y
    return "".join(out)


def _syllable_spans(lines, ws, li: int, ks: list[tuple[int, str]]) -> list[tuple[int, int, str]]:
    spans, w = [], ws[li]
    for k, c in ks:
        kl = lines[li].ks[k]
        n = sum(1 for o in lines[li].ks if o.word == kl.word)
        if kl.word < len(w):
            a, b = syllable_chars(w.form[kl.word], n)[kl.syl]
            spans.append((w.a[kl.word] + a, w.a[kl.word] + b, c))
    return spans


def html() -> str:
    """A page with every line marked three ways: the reference, line_pairs.py and the probability model (full
    lyrics, local only, data/rhyme_view). The probability model uses weights fitted on all songs here, so it looks
    better than in its honest leave-one-song-out validation (config/rhyme_probability.yaml). The page text is Polish."""
    from rapdna.experiments import line_pairs, probability
    from rapdna.validate.recordings import meter_for_rows

    data, words = load_marks()
    parts = []
    groups = sorted({m["group"] for d in data.values() for m in d["marks"]})
    colour = {g: PALETTE[k % len(PALETTE)] for k, g in enumerate(groups)}
    for title, sid, sec, ris, ws, lines, marks in sections(data, words):
        meter = meter_for_rows(sid, ws, lines)
        auto, prob = defaultdict(list), defaultdict(list)
        for cell, gid in line_pairs.mark(lines):
            auto[cell.line] += [(k, PALETTE[gid % len(PALETTE)]) for k in range(cell.start, cell.end)]
        for cell, gid, _ in probability.mark(lines, meter):
            prob[cell.line] += [(k, PALETTE[gid % len(PALETTE)]) for k in range(cell.start, cell.end)]
        rows_html = []
        for li, ri in enumerate(ris):
            text = data[title]["rows"][ri]["text"]
            gold = [(m["i"], m["j"], colour[m["group"]]) for m in marks[li]]
            rows_html.append(f"<tr><td>{_paint(text, gold)}</td><td>{_paint(text, _syllable_spans(lines, ws, li, auto[li]))}"
                             f"</td><td>{_paint(text, _syllable_spans(lines, ws, li, prob[li]))}</td></tr>")
        parts.append(f"<h2>{title} – sekcja {sec}</h2><table><tr><th>oznaczenia</th>"
                     f"<th>pary wersów</th><th>model szansy</th></tr>{''.join(rows_html)}</table>")
    page = ("<!doctype html><meta charset=utf-8><title>Oznaczenia a automat</title><style>body{font:15px/1.6 'DejaVu Sans',"
            "sans-serif;background:#e6e6e6;margin:16px}td{padding:2px 12px;white-space:nowrap}h2{font-size:17px}"
            "table{border-collapse:collapse;margin-bottom:24px}th{text-align:left}</style>"
            "<h1>Oznaczenia rymów a automat</h1><p>Kolumny: oznaczenia wzorcowe, experiments/line_pairs.py (ciągi rymów "
            "w parach sąsiednich wersów), experiments/probability.py (model szansy rymu; wagi uczone na tych samych "
            "utworach, więc tu wygląda lepiej niż w walidacji). Kolor = grupa rymu; granice sylab w zapisie są "
            "przybliżone.</p>" + "".join(parts))
    out = paths.DATA / "rhyme_view" / "annotations_vs_methods.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    from rapdna.experiments import feet, line_pairs

    secs = gold_sections()
    for name, mark in (("feet.mark(strict=True)", lambda ls: feet.mark(ls)),
                       ("feet.mark(strict=False)", lambda ls: feet.mark(ls, strict=False)),
                       ("line_pairs.mark", line_pairs.mark)):
        print(name, score(secs, [mark(s["lines"]) for s in secs]))
    print("Page:", html())
