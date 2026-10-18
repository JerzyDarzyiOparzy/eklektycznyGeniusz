"""Local karaoke page for checking the alignment by ear:
highlighted words, a click on every beat, marking lines that are „out of time”. Full lyrics: local only, never
publish. The page text is Polish."""
import base64
import json
import subprocess
from html import escape

from rapdna.audio import ALIGN, RAW, VIEW, VOCALS
from rapdna.audio.overrides import PRON

_PAGE = """<!doctype html>
<html lang="pl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Odsłuch: __TITLE__</title>
<style>
:root { --bg:#fbfaf7; --fg:#1d1d1b; --mut:#77746c; --hi:#ffd84d; --bad:#e5484d; --line:#e7e3da; }
@media (prefers-color-scheme: dark) { :root { --bg:#171716; --fg:#ecebe6; --mut:#9a978e; --hi:#8a6d00; --line:#2c2b28; } }
body { background:var(--bg); color:var(--fg); font:17px/1.6 system-ui, sans-serif; margin:0; padding:0 16px 120px; }
header { position:sticky; top:0; background:var(--bg); padding:12px 0; border-bottom:1px solid var(--line); z-index:1; }
h1 { font-size:18px; margin:0 0 8px; } .mut { color:var(--mut); font-size:14px; }
.ctl { display:flex; flex-wrap:wrap; gap:8px; align-items:center; } button, label { font:inherit; font-size:14px; }
button { border:1px solid var(--line); background:transparent; color:var(--fg); border-radius:6px; padding:4px 10px; cursor:pointer; }
audio { width:100%; margin-top:8px; }
#beat { width:14px; height:14px; border-radius:50%; background:var(--line); display:inline-block; }
#beat.on { background:var(--fg); } #beat.down { background:var(--bad); }
section { margin-top:22px; } h2 { font-size:14px; color:var(--mut); font-weight:600; margin:0 0 4px; }
.l { display:flex; gap:8px; align-items:baseline; padding:1px 0; } .l.bad .t { text-decoration:underline wavy var(--bad); }
.l button { padding:0 6px; font-size:12px; opacity:.5; } .l.bad button { opacity:1; color:var(--bad); border-color:var(--bad); }
.w { cursor:pointer; border-radius:3px; padding:0 1px; } .w.now { background:var(--hi); } .w.low { color:var(--mut); }
.w.pron { border-bottom:2px dotted var(--bad); } .w.pron.sw { border-bottom-style:solid; }
</style></head><body>
<header>
<h1>__TITLE__</h1>
<div class="mut">Klik w słowo przewija nagranie. Szare słowa: niska pewność wyrównania. Oznacz wersy, które podświetlają się
nie w czasie, potem „Kopiuj wynik” i zapisz go. Podkreślone słowa: wymowę rozstrzygało nagranie
(ciągła linia – nagranie zmieniło odczyt z reguł); najedź, żeby zobaczyć oba zapisy.</div>
<div class="ctl" style="margin-top:8px">
<label><input type="radio" name="src" value="mix" checked> całe nagranie</label>
<label><input type="radio" name="src" value="voc"> sam wokal</label>
<label><input type="checkbox" id="click"> klik na bitach</label>
<span id="beat" title="bit / pierwszy bit taktu"></span>
<span class="mut" id="sum"></span>
<button id="copy">Kopiuj wynik</button>
</div>
<audio id="a" controls preload="auto"></audio>
</header>
<main id="m"></main>
<script>
const D = __DATA__;
const a = document.getElementById('a'), m = document.getElementById('m');
const src = {mix: '__MIX__', voc: '__VOC__'};
a.src = src.mix;
let bad = new Set();
try { bad = new Set(JSON.parse(localStorage.getItem('bad-' + D.song_id) || '[]')); } catch (e) {}
const save = () => { try { localStorage.setItem('bad-' + D.song_id, JSON.stringify([...bad])); } catch (e) {} ;
  document.getElementById('sum').textContent = `nie w czasie: ${bad.size} z ${nLines} wersów`; };
const spans = []; let nLines = 0, sec = null, cur = null, lineEl = null, lineId = null;
for (const w of D.words) {
  if (w.section !== sec) { sec = w.section; cur = document.createElement('section');
    cur.innerHTML = `<h2>${w.section_type || 'sekcja'}${w.performers ? ': ' + w.performers : ''}</h2>`; m.append(cur); }
  if (w.line_uid !== lineId) { lineId = w.line_uid; nLines++;
    lineEl = document.createElement('div'); lineEl.className = 'l' + (bad.has(lineId) ? ' bad' : '');
    const b = document.createElement('button'); b.textContent = '×'; b.title = 'nie w czasie';
    const id = lineId, el = lineEl;
    b.onclick = () => { bad.has(id) ? bad.delete(id) : bad.add(id); el.classList.toggle('bad'); save(); };
    const t = document.createElement('span'); t.className = 't'; lineEl.append(b, t); cur.append(lineEl); }
  const s = document.createElement('span'); s.className = 'w' + (w.score < 0.35 ? ' low' : '');
  s.textContent = w.form; s.title = `${w.start.toFixed(2)}–${w.end.toFixed(2)} s, pewność ${w.score.toFixed(2)}`;
  const pr = (D.pron || {})[w.line_uid + ':' + w.w];
  if (pr) { s.classList.add('pron'); if (pr.lang !== pr.rules_lang) s.classList.add('sw');
    s.title += `
reguły: ${pr.rules_lang} | nagranie: ${pr.lang} („${pr.spell[pr.lang]}”, nie „${pr.spell[pr.lang === 'pl' ? 'en' : 'pl']}”), różnica ${pr.margin.toFixed(1)}`; }
  s.onclick = () => { a.currentTime = Math.max(0, w.start - 0.3); a.play(); };
  lineEl.querySelector('.t').append(s, ' '); spans.push([w.start, w.end, s]);
}
save();
document.querySelectorAll('input[name=src]').forEach(r => r.onchange = () => {
  const t = a.currentTime, p = !a.paused; a.src = src[r.value]; a.currentTime = t; if (p) a.play(); });
document.getElementById('copy').onclick = () => {
  const txt = JSON.stringify({song_id: D.song_id, wersy: nLines, nie_w_czasie: [...bad]});
  navigator.clipboard.writeText(txt).then(() => alert_('skopiowano'), () => prompt_(txt)); };
const alert_ = t => { document.getElementById('sum').textContent = t; setTimeout(save, 1500); };
const prompt_ = t => { const x = document.createElement('textarea'); x.value = t; x.style.width = '100%'; m.prepend(x); x.select(); };
let ctx = null, bi = 0, now = null;
const dot = document.getElementById('beat'), down = new Set(D.downbeats.map(t => t.toFixed(3)));
function tick() {
  const t = a.currentTime;
  if (now && !(t >= now[0] && t < now[1] + 0.05)) { now[2].classList.remove('now'); now = null; }
  if (!now) { for (const sp of spans) if (t >= sp[0] && t < sp[1] + 0.05) { now = sp; sp[2].classList.add('now'); break; } }
  while (bi < D.beats.length && D.beats[bi] < t - 0.05) bi++;
  if (bi < D.beats.length && Math.abs(D.beats[bi] - t) < 0.06) {
    const isDown = down.has(D.beats[bi].toFixed(3));
    dot.className = isDown ? 'down' : 'on';
    if (document.getElementById('click').checked && !a.paused) { click(isDown); }
    bi++; setTimeout(() => dot.className = '', 90);
  }
  requestAnimationFrame(tick);
}
function click(isDown) {
  ctx = ctx || new AudioContext(); const o = ctx.createOscillator(), g = ctx.createGain();
  o.frequency.value = isDown ? 1600 : 1000; g.gain.setValueAtTime(0.3, ctx.currentTime);
  g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05); o.connect(g).connect(ctx.destination);
  o.start(); o.stop(ctx.currentTime + 0.06);
}
a.onseeked = () => { bi = 0; };
requestAnimationFrame(tick);
</script></body></html>
"""


def _mp3_data_uri(path) -> str:
    """Audio embedded in the page (MP3 128 kb/s): relative paths to WAV files did not play when the page was opened
    from disk."""
    mp3 = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-b:a", "128k", "-f", "mp3", "-"],
                         capture_output=True, check=True).stdout
    return "data:audio/mpeg;base64," + base64.b64encode(mp3).decode("ascii")


def build(song_id: int, title: str) -> str:
    data = json.loads((ALIGN / f"{song_id}.json").read_text(encoding="utf-8"))
    cand = PRON / f"{song_id}.candidates.json"
    if cand.exists():
        data["pron"] = {f"{d['line_uid']}:{d['w']}": d for d in json.loads(cand.read_text(encoding="utf-8"))}
    VIEW.mkdir(parents=True, exist_ok=True)
    out = VIEW / f"{song_id}.html"
    html = (_PAGE.replace("__TITLE__", escape(title)).replace("__DATA__", json.dumps(data, ensure_ascii=False))
            .replace("__MIX__", _mp3_data_uri(RAW / f"{song_id}.wav"))
            .replace("__VOC__", _mp3_data_uri(VOCALS / f"{song_id}.wav")))
    out.write_text(html, encoding="utf-8")
    return str(out)
