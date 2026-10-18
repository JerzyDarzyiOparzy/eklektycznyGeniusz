"""Experiment: a map of rhyme units as an HTML page to look at (docs/en/internal-rhymes.md).

Points: the most frequent units projected onto a plane (`units.project`). Close = they rhyme well. Point size: number
of occurrences. Hover: example words and the 5 best rhymes of the unit. The page text is Polish.
"""
import json
from collections import Counter

import numpy as np

from rapdna.experiments.units import OUT, Unit, neighbors, project

TEMPLATE = """<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mapa klocków rymowych</title>
<style>
:root { --plane:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781; --grid:#e1e0d9;
  --axis:#c3c2b7; --border:rgba(11,11,11,.10); --s1:#2a78d6; --dim:#d4d3cc; color-scheme:light; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --plane:#0d0d0d; --surface:#1a1a19; --ink:#f0efec;
  --ink-2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10); --s1:#3987e5;
  --dim:#3a3a37; color-scheme:dark; } }
:root[data-theme="dark"] { --plane:#0d0d0d; --surface:#1a1a19; --ink:#f0efec; --ink-2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,.10); --s1:#3987e5; --dim:#3a3a37; color-scheme:dark; }
* { box-sizing:border-box; }
body { margin:0; padding:24px 16px 48px; background:var(--plane); color:var(--ink);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; }
.wrap { max-width:1040px; margin:0 auto; display:flex; flex-direction:column; gap:16px; }
h1 { margin:0; font-size:1.6rem; } p { margin:0; max-width:70ch; color:var(--ink-2); }
.panel { background:var(--surface); border:1px solid var(--border); border-radius:6px; padding:16px; }
.controls { display:flex; gap:12px; align-items:end; flex-wrap:wrap; }
label { display:flex; flex-direction:column; gap:4px; font-size:.8rem; color:var(--ink-2); }
select { font:inherit; color:var(--ink); background:var(--surface); border:1px solid var(--axis); border-radius:4px; padding:5px 8px; }
svg { width:100%; height:auto; display:block; }
.lbl { font:11px ui-monospace,Consolas,monospace; fill:var(--ink-2); pointer-events:none; }
circle { stroke:var(--surface); stroke-width:2; cursor:default; }
#tip { position:fixed; pointer-events:none; z-index:5; max-width:280px; background:var(--surface); color:var(--ink);
  border:1px solid var(--axis); border-radius:4px; padding:8px 10px; font-size:.8rem; box-shadow:0 4px 14px rgba(0,0,0,.12); }
#tip b { font-family:ui-monospace,Consolas,monospace; }
table { border-collapse:collapse; font-size:.82rem; width:100%; }
td, th { text-align:left; padding:4px 6px; border-bottom:1px solid var(--grid); vertical-align:top; }
th { color:var(--muted); font-weight:500; }
td.m { font-family:ui-monospace,Consolas,monospace; white-space:nowrap; }
</style></head><body>
<div class="wrap">
  <h1>Mapa klocków rymowych</h1>
  <p>Każdy punkt to klocek: samogłoska i spółgłoski po niej aż do następnej samogłoski („tango” = [aŋɡ] [ɔ]).
  Klocki stojące blisko dobrze się ze sobą rymują według modelu Hirjee i Browna (wariant A). Rozmiar punktu to liczba
  wystąpień w korpusie. Pokazane jest __N__ najczęstszych klocków (__COVER__% wszystkich wystąpień). Rzut na płaszczyznę
  zniekształca odległości, więc dokładne oceny są w podpowiedzi i w tabeli.</p>
  <div class="panel">
    <div class="controls"><label for="vow">Wyróżnij samogłoskę <select id="vow"><option value="">wszystkie</option></select></label></div>
    <svg id="map" viewBox="0 0 1000 680" role="img" aria-label="Mapa klocków rymowych"></svg>
  </div>
  <details class="panel"><summary>Tabela: klocki i ich najlepsze rymy</summary>
    <table><thead><tr><th>klocek</th><th>wystąpień</th><th>przykłady</th><th>5 najlepszych rymów (ocena)</th></tr></thead><tbody id="tbl"></tbody></table>
  </details>
</div>
<div id="tip" hidden></div>
<script>
const D = __DATA__;
const svg = document.getElementById("map"), tip = document.getElementById("tip"), NS = "http://www.w3.org/2000/svg";
const xs = D.map(d => d.x), ys = D.map(d => d.y), pad = 40;
const sx = v => pad + (v - Math.min(...xs)) / (Math.max(...xs) - Math.min(...xs)) * (1000 - 2 * pad);
const sy = v => pad + (v - Math.min(...ys)) / (Math.max(...ys) - Math.min(...ys)) * (680 - 2 * pad);
const maxN = Math.max(...D.map(d => d.n));
const dots = D.map((d, i) => {
  const c = document.createElementNS(NS, "circle");
  c.setAttribute("cx", sx(d.x)); c.setAttribute("cy", sy(d.y)); c.setAttribute("r", 4 + 14 * Math.sqrt(d.n / maxN));
  c.addEventListener("mousemove", e => {
    tip.innerHTML = `<b>[${d.u}]</b> · ${d.n.toLocaleString("pl")} wystąpień<br>${d.ex.join(", ") || "-"}<br><br>` +
      d.nb.map(([u, s]) => `<b>[${u}]</b> ${s > 0 ? "+" : ""}${s.toFixed(2)}`).join("<br>");
    tip.hidden = false; tip.style.left = Math.min(e.clientX + 14, innerWidth - 300) + "px"; tip.style.top = (e.clientY + 14) + "px";
  });
  c.addEventListener("mouseleave", () => tip.hidden = true);
  svg.appendChild(c);
  return c;
});
// labels from the most frequent unit; skip those that would cover one already placed (full list in tooltip and table)
const placed = [];
D.forEach((d, i) => { if (i >= 80) return;
  const x = sx(d.x) + 7 + 14 * Math.sqrt(d.n / maxN), y = sy(d.y) + 4, box = [x - 2, y - 11, x + 7 * d.u.length + 2, y + 3];
  if (placed.some(b => box[0] < b[2] && b[0] < box[2] && box[1] < b[3] && b[1] < box[3])) return;
  placed.push(box);
  const t = document.createElementNS(NS, "text");
  t.setAttribute("class", "lbl"); t.setAttribute("x", x); t.setAttribute("y", y); t.textContent = d.u; svg.appendChild(t); });
const sel = document.getElementById("vow");
[...new Set(D.map(d => d.v))].forEach(v => sel.add(new Option(v, v)));
const paint = () => dots.forEach((c, i) => c.setAttribute("fill", !sel.value || D[i].v === sel.value ? "var(--s1)" : "var(--dim)"));
sel.addEventListener("change", paint); paint();
document.getElementById("tbl").innerHTML = D.map(d => `<tr><td class="m">[${d.u}]</td><td>${d.n.toLocaleString("pl")}</td>` +
  `<td>${d.ex.join(", ")}</td><td class="m">${d.nb.map(([u, s]) => `[${u}] ${s.toFixed(2)}`).join(" · ")}</td></tr>`).join("");
</script></body></html>
"""


def write(us: list[Unit], m: np.ndarray, counts: Counter, examples: dict[Unit, list[str]], n: int = 300) -> str:
    xy = project(m, n)
    total = sum(counts.values())
    data = [{"u": str(u), "v": u.vowel, "n": counts[u], "x": round(float(xy[i, 0]), 3), "y": round(float(xy[i, 1]), 3),
             "ex": examples.get(u, []), "nb": [[str(us[j]), round(float(m[i, j]), 2)] for j in neighbors(us, m, counts, i)]}
            for i, u in enumerate(us[:n])]
    cover = round(100 * sum(counts[u] for u in us[:n]) / total, 1)
    html = (TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__N__", str(n)).replace("__COVER__", str(cover).replace(".", ",")))
    path = OUT / "mapa.html"
    path.write_text(html, encoding="utf-8")
    return str(path)
