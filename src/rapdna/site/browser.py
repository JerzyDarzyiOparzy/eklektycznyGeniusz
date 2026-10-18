"""Local song browser with stylistic devices marked (layers that can be switched on and off).

Every corpus song: the whole text, guest lines greyed out, and in the rapper's lines the marks from the same methods
that compute the statistics: end rhymes (syllables + the scheme in a separate column), internal rhymes (a separate
layer and letters), anaphora, epiphora, alliteration, phrase repetition and confirmed wordplay. It shows full lyrics,
so it never goes on the public page: the file lands in data/ (gitignored) and is for checking by eye what the methods
mark. The page text is Polish.
"""
import json
import re

import pandas as pd

from rapdna import paths
from rapdna.figures.repetition import ANAPHORA_STOP, is_anaphora, is_epiphora, phrase_repetition_words
from rapdna.figures.sound import find_alliterations
from rapdna.experiments.families import families
from rapdna.rhymes.match import build_line, thresholds
from rapdna.text.ortho import syllables
from rapdna.text.sections import norm_line

OUT = paths.DATA / "rhyme_view" / "songs.html"


def _puns() -> tuple[dict, dict]:
    """Confirmed wordplay: (rapper, title, normalised line) → explanation; paronomasia → the pair of words."""
    k = paths.DATA / "candidates"
    ann = pd.read_csv(k / "wordplay_review.csv", sep=";", encoding="utf-8-sig")
    notes = {}
    for r in ann[ann.confirmed == 1].itertuples():
        for ln in str(r.fragment).split(" / "):
            notes[(r.artist, r.title, norm_line(ln))] = re.sub(r"\s+", " ", str(r.annotation))[:320]
    par = pd.read_csv(k / "paronomasia_review.csv", sep=";", encoding="utf-8-sig")
    pairs = {(r.artist, r.title, norm_line(r.text)): {r.word_a.lower(), r.word_b.lower()}
             for r in par[par.confirmed == 1].itertuples()}
    return notes, pairs


def _song(g: pd.DataFrame, by: dict, th: dict, notes: dict, pairs: dict) -> dict:
    artist, title = g.artist.iloc[0], g.title.iloc[0]
    sections = []
    for _, s in g.groupby("section", sort=True):
        s = s.sort_values("line")
        rows = [{"own": bool(r.attributed and not r.is_dup), "text": r.text, "uid": r.line_uid} for r in s.itertuples()]
        words = [by.get(r["uid"], []) for r in rows]
        own_idx = [i for i, r in enumerate(rows) if r["own"] and words[i]]
        built = {i: build_line(words[i]) for i in own_idx}
        seq = [built[i] for i in own_idx]
        marks = {i: {"end": {}, "int": {}} for i in own_idx}  # line → layer → (word, syllable) → family
        letters = {}
        for layer, kind in (("end", "end"), ("int", "internal")):
            f = families(seq, th, kind=kind)
            for sp, fam in zip(f.spans, f.family):
                i = own_idx[sp.line]
                for k in range(sp.k0, sp.k1 + 1):
                    kk = built[i].ks[k]
                    marks[i][layer].setdefault((kk.word, kk.syl), fam)
            if layer == "end":
                letters = {own_idx[li]: ch for li, ch in enumerate(f.scheme)}
        out_lines, prev = [], None
        for i, r in enumerate(rows):
            w = words[i]
            forms = [x[0] for x in w]
            low = [f.lower() for f in forms]
            line = {"own": r["own"], "end": letters.get(i, ""), "fig": {}, "pun": None, "w": []}
            if r["own"] and w:
                ln = built[i]
                nsyl = {wi: sum(1 for k in ln.ks if k.word == wi) for wi in range(len(w))}
                content = [not (x[3] in {"ADP", "CCONJ", "SCONJ", "PART", "PRON", "DET", "INTJ", "AUX"}) for x in w]
                if prev is not None:
                    pl = [x[0].lower() for x in words[prev]]
                    if is_anaphora(pl, low):
                        line["fig"]["anaphora"] = [0, 1] if low[0] in ANAPHORA_STOP else [0]
                    if is_epiphora(pl, low):
                        line["fig"]["epiphora"] = [len(low) - 1]
                    rep = phrase_repetition_words(pl, low, content)
                    if rep:
                        line["fig"]["repetition"] = sorted(rep)
                ali = find_alliterations([(x[0], x[2], x[1], not c) for x, c in zip(w, content)])
                if ali:
                    line["fig"]["alliteration"] = sorted({k for a in ali for k in a.words})
                key = (artist, title, norm_line(r["text"]))
                if key in notes:
                    line["pun"] = notes[key]
                if key in pairs:
                    line["fig"]["pun"] = [k for k, f in enumerate(low) if f in pairs[key]]
                    line["pun"] = line["pun"] or "paronomazja (podobnie brzmiące słowa)"
                for wi, form in enumerate(forms):
                    parts = syllables(form, nsyl.get(wi, 1))
                    whole = len(parts) == 1 and nsyl.get(wi, 1) > 1
                    syl = []
                    for si, part in enumerate(parts):
                        ids = range(nsyl[wi]) if whole else [si]
                        e = next((marks[i]["end"][(wi, x)] for x in ids if (wi, x) in marks[i]["end"]), None)
                        n = next((marks[i]["int"][(wi, x)] for x in ids if (wi, x) in marks[i]["int"]), None)
                        syl.append([part, e, n])
                    line["w"].append(syl)
                prev = i
            else:
                line["w"] = [[[f, None, None]] for f in (forms or r["text"].split())]
            out_lines.append(line)
        sections.append(out_lines)
    return {"artist": artist, "title": title, "album": g.album.iloc[0], "year": int(g.year.dropna().iloc[0]) if g.year.notna().any() else None,
            "sections": sections}


def build(log=print) -> str:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet").sort_values(["line_uid", "w"])
    by = {u: list(zip(g.form, g.ipa, g.lemma, g.pos)) for u, g in words.groupby("line_uid")}
    th = thresholds()
    notes, pairs = _puns()
    songs = []
    groups = lines.groupby("song_id", sort=False)
    for n, (_, g) in enumerate(groups):
        songs.append(_song(g, by, th, notes, pairs))
        if n % 200 == 0:
            log(f"  songs: {n}/{groups.ngroups}")
    songs.sort(key=lambda s: (s["artist"], s["year"] or 0, s["album"], s["title"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(TEMPLATE.replace("__DATA__", json.dumps(songs, ensure_ascii=False, separators=(",", ":"))), encoding="utf-8")
    return str(OUT)


TEMPLATE = r"""<!doctype html><html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Przeglądarka utworów</title><style>
:root { --plane:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781; --border:rgba(11,11,11,.10);
  --ana:#2a78d6; --epi:#eb6834; --ali:#1b8a5a; --rep:#6250d6; --pun:#c0392b; color-scheme:light; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --plane:#0d0d0d; --surface:#1a1a19; --ink:#f0efec;
  --ink-2:#c3c2b7; --muted:#898781; --border:rgba(255,255,255,.12); --ana:#3987e5; --epi:#d95926; --ali:#199e70; --rep:#9085e9;
  --pun:#e66767; color-scheme:dark; } }
* { box-sizing:border-box; }
body { margin:0; padding:20px 16px 48px; background:var(--plane); color:var(--ink); font:16px/1.75 system-ui,-apple-system,"Segoe UI",sans-serif; }
.wrap { max-width:960px; margin:0 auto; display:flex; flex-direction:column; gap:14px; }
h1 { margin:0; font-size:1.4rem; } p { margin:0; color:var(--ink-2); max-width:75ch; font-size:.92rem; }
.bar { display:flex; flex-wrap:wrap; gap:10px; align-items:end; }
label.sel { display:flex; flex-direction:column; font-size:.8rem; color:var(--ink-2); gap:3px; }
select { font:inherit; font-size:.92rem; padding:5px 8px; border:1px solid #c3c2b7; border-radius:4px; background:var(--surface); color:var(--ink); max-width:100%; }
.layers { display:flex; flex-wrap:wrap; gap:6px 14px; font-size:.86rem; }
.layers label { display:flex; gap:6px; align-items:center; cursor:pointer; }
.key { display:inline-block; min-width:22px; text-align:center; border-radius:3px; font-size:.75rem; padding:0 4px; }
.song { background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:14px 16px; }
.sec { margin-top:12px; padding-top:8px; border-top:1px dashed var(--border); }
.sec:first-child { border-top:0; margin-top:0; padding-top:0; }
.ln { display:grid; grid-template-columns:7.5rem minmax(0,1fr) 2rem; gap:10px; align-items:baseline; }
.ln.guest { color:var(--muted); font-style:italic; }
.figs { font-size:.68rem; color:var(--muted); display:flex; flex-wrap:wrap; gap:2px; justify-content:flex-end; }
.chip { border-radius:999px; padding:0 6px; border:1px solid currentColor; line-height:1.5; }
.scheme { font-family:ui-monospace,Consolas,monospace; font-weight:600; text-align:center; border-radius:3px; }
.w { white-space:nowrap; } .s { border-radius:3px; padding:0 1px; }
.s.int { box-shadow:inset 0 -3px 0 var(--u); }
.fw-ana { outline:2px solid var(--ana); outline-offset:1px; border-radius:2px; }
.fw-epi { outline:2px dashed var(--epi); outline-offset:1px; border-radius:2px; }
.fw-ali { color:var(--ali); font-weight:700; }
.fw-rep { text-decoration:underline dotted var(--rep) 2px; text-underline-offset:4px; }
.fw-gra { color:var(--pun); font-weight:700; }
.pun { cursor:help; color:var(--pun); }
.legend { font-size:.8rem; color:var(--ink-2); }
</style></head><body><div class="wrap">
<h1>Przeglądarka utworów</h1>
<p>Oznaczenia z tych samych metod, które liczą statystyki. Każda warstwa osobno: włączaj po jednej, żeby sprawdzić, co
automat zaznacza. Szare wersy należą do gości i nie są analizowane. Plik lokalny z pełnymi tekstami – nie publikować.</p>
<div class="bar">
  <label class="sel" for="artist">Raper <select id="artist"></select></label>
  <label class="sel" for="song">Utwór <select id="song"></select></label>
</div>
<div class="layers" id="layers"></div>
<div class="legend" id="legend"></div>
<div class="song" id="view"></div>
</div>
<script>
const S = __DATA__;
const END = ["#cfe1f7","#fbd6c5","#c4ecdc","#fbe3a6","#f6d2e1","#cfe8c4","#ddd7f5","#f7cccb","#d6eef3","#efe0c9","#e3e3e3","#f1d9f3"];
const INT = ["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4","#008300","#6250d6","#e34948"];
const LAYERS = [
  ["end", "Rymy końcowe (sylaby + schemat)", "rym końcowy"], ["int", "Rymy wewnętrzne", "rym wewnętrzny"],
  ["anaphora", "Anafory", "anafora"], ["epiphora", "Epifory", "epifora"], ["alliteration", "Aliteracje", "aliteracja"],
  ["repetition", "Powtórzenia fraz", "powtórzenie"], ["pun", "Gry słów", "gra słów"]];
const on = { end: true, int: false, anaphora: false, epiphora: false, alliteration: false, repetition: false, pun: false };
const esc = t => String(t).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const L = (f, up) => { const c = f < 26 ? String.fromCharCode(65 + f) : "Z" + (f - 25); return up ? c : c.toLowerCase(); };
const artists = [...new Set(S.map(s => s.artist))];
const aSel = document.getElementById("artist"), sSel = document.getElementById("song");
aSel.innerHTML = artists.map(a => `<option>${esc(a)}</option>`).join("");
function fillSongs() {
  sSel.innerHTML = S.map((s, i) => [s, i]).filter(([s]) => s.artist === aSel.value)
    .map(([s, i]) => `<option value="${i}">${s.year || ""} · ${esc(s.album)} – ${esc(s.title)}</option>`).join("");
}
document.getElementById("layers").innerHTML = LAYERS.map(([k, name]) =>
  `<label><input type="checkbox" data-k="${k}" ${on[k] ? "checked" : ""}>${name}</label>`).join("");
function legend() {
  const parts = [];
  if (on.end) parts.push(`<b>Rymy końcowe:</b> sylaby tej samej rodziny mają jedno tło, litera z prawej to schemat zwrotki (A, B, C…; „-” = koniec bez rymu).`);
  if (on.int) parts.push(`<b>Rymy wewnętrzne:</b> kolorowe podkreślenie sylab, osobne rodziny (litery małe w podpowiedzi).`);
  if (on.anaphora) parts.push(`<span class="fw-ana">anafora</span> – ten sam początek co poprzedni wers rapera.`);
  if (on.epiphora) parts.push(`<span class="fw-epi">epifora</span> – ten sam koniec.`);
  if (on.alliteration) parts.push(`<span class="fw-ali">aliteracja</span> – ta sama pierwsza głoska.`);
  if (on.repetition) parts.push(`<span class="fw-rep">powtórzenie frazy</span>.`);
  if (on.pun) parts.push(`<span class="fw-gra">gra słów</span> – najedź na *, żeby zobaczyć objaśnienie.`);
  document.getElementById("legend").innerHTML = parts.join(" · ") || "Włącz warstwę, żeby zobaczyć oznaczenia.";
}
function render() {
  const s = S[+sSel.value]; if (!s) return;
  const html = s.sections.map(sec => `<div class="sec">${sec.map(ln => {
    if (!ln.own) return `<div class="ln guest"><span></span><span>${ln.w.map(w => esc(w[0][0])).join(" ")}</span><span></span></div>`;
    const figs = Object.keys(ln.fig).filter(k => on[k]);
    const chips = figs.map(k => `<span class="chip">${LAYERS.find(x => x[0] === k)[2]}</span>`).join("");
    const wordHtml = ln.w.map((syl, wi) => {
      const cls = figs.filter(k => ln.fig[k].includes(wi)).map(k => ({ anaphora: "fw-ana", epiphora: "fw-epi", alliteration: "fw-ali", repetition: "fw-rep", pun: "fw-gra" })[k]).join(" ");
      const inner = syl.map(([t, e, n]) => {
        const st = [], c = ["s"]; let tip = [];
        if (on.end && e !== null) { st.push(`background:${END[e % END.length]}`); tip.push("rym końcowy " + L(e, true)); }
        if (on.int && n !== null) { st.push(`--u:${INT[n % INT.length]}`); c.push("int"); tip.push("rym wewnętrzny " + L(n, false)); }
        return st.length ? `<span class="${c.join(" ")}" style="${st.join(";")}" title="${tip.join(", ")}">${esc(t)}</span>` : esc(t);
      }).join("");
      return `<span class="w ${cls}">${inner}</span>`;
    }).join(" ");
    const pun = on.pun && ln.pun ? ` <span class="pun" title="${esc(ln.pun)}">*</span>` : "";
    const sch = on.end && ln.end ? `<span class="scheme" style="${ln.end !== "-" ? `background:${END[(ln.end.charCodeAt(0) - 65) % END.length]}` : ""}">${esc(ln.end)}</span>` : "<span></span>";
    return `<div class="ln"><span class="figs">${chips}</span><span>${wordHtml}${pun}</span>${sch}</div>`;
  }).join("")}</div>`).join("");
  document.getElementById("view").innerHTML = `<h2 style="margin:0 0 8px;font-size:1.1rem">${esc(s.artist)} – ${esc(s.title)}</h2>` + html;
}
document.getElementById("layers").addEventListener("change", e => { on[e.target.dataset.k] = e.target.checked; legend(); render(); });
aSel.addEventListener("change", () => { fillSongs(); render(); });
sSel.addEventListener("change", render);
fillSongs(); legend(); render();
</script></body></html>
"""
