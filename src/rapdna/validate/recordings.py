"""Recordings of the annotated songs (outside the corpus): YouTube → vocals → beats → alignment of the full Genius
lyrics. The same pipeline as `rapdna audio` (recordings stay local). Output: data/audio/align/<id>.json.

Usage: python -m rapdna.validate.recordings
"""
import bisect
import difflib
import json
import string

import pandas as pd

from rapdna.audio import ALIGN, align, fetch, signal
from rapdna.audio.syllable_time import syllable_onsets
from rapdna.text.phonetics import tokenize
from rapdna.validate.annotations import SONGS, genius_lines

# YouTube queries for when the video title does not match the performer's name on YouTube
QUERY = {"Pores & Nullo & Szad - Dla Mnie Masz Stajla": ("Trzeci Wymiar", "Dla mnie masz stajla"),
         "Eripe - Mogę Wypierdalać (100 Linijek Szaleństwa 3)": ("Eripe", "Mogę wypierdalać"),
         "Tepesz & Okoń - Biszkopcik": ("rów babicze", "Biszkopcik"),
         "Quebonafide & Smarki Smark - COJESTMAŁPY": ("Quebonafide", "COJESTMAŁPY")}
LABELS = set(string.ascii_lowercase) | {"'"}  # letters of the MMS vocabulary (Latin without diacritics)


def song_words(song_id: int) -> pd.DataFrame:
    rows = []
    for gi, g in enumerate(genius_lines(song_id)):
        for wi, form in enumerate(tokenize(g["text"])):
            rows.append({"gl": gi, "section": g["section"], "line": g["line"], "w": wi, "form": form, "text": g["text"]})
    return pd.DataFrame(rows)


def run(device: str = "cuda"):
    songs = json.loads(SONGS.read_text(encoding="utf-8"))
    for title, meta in songs.items():
        sid = meta["song_id"]
        if (ALIGN / f"{sid}.json").exists():
            print(f"{title}: already aligned", flush=True)
            continue
        artist, name = QUERY.get(title, title.split(" - ", 1))
        artist = artist.split(" & ")[0]
        try:
            raw = fetch.download(sid, artist, name)
            if raw is None:
                print(f"{title}: no recording", flush=True)
                continue
            vocals = signal.separate_vocals(raw, sid, device)
            beats, downbeats = signal.beats(raw, device)
            words = align.align(sid, vocals, device, words=song_words(sid))
            align.save(sid, words, beats, downbeats)
            print(f"{title}: words {len(words)}, confidence {words.score.mean():.2f}, beats {len(beats)}", flush=True)
        except Exception as e:  # one bad song does not stop the rest
            print(f"{title}: error {e!r}", flush=True)


def position16(t: float, beats: list[float], downbeats: list[float]) -> int | None:
    """Position of moment t in the bar: 0–15 (sixteenths from „one”), None outside the beats."""
    b = bisect.bisect_right(beats, t) - 1
    if b < 0 or b + 1 >= len(beats):
        return None
    six = round(4 * (t - beats[b]) / (beats[b + 1] - beats[b]))
    if six == 4:
        b, six = b + 1, 0
    d = bisect.bisect_right(downbeats, beats[b] + 1e-3) - 1
    if d < 0:
        return None
    beat_in_bar = sum(1 for x in beats if downbeats[d] - 1e-3 <= x < beats[b] - 1e-3)
    return (beat_in_bar % 4) * 4 + six


def meter_for_rows(song_id: int, rows: list[pd.DataFrame], lines) -> list[list[int | None]] | None:
    """For annotated lines (words: form, ipa): the bar position of every syllable (unit), or None without a
    recording. Line words are matched to the aligned words of the whole song by order (difflib)."""
    f = ALIGN / f"{song_id}.json"
    if not f.exists():
        return None
    al = json.loads(f.read_text(encoding="utf-8"))
    aw = al["words"]
    flat = [(li, wi) for li, w in enumerate(rows) for wi in range(len(w))]
    a = [x["form"].lower() for x in aw]
    b = [rows[li].form.iloc[wi].lower() for li, wi in flat]
    match = {}
    for i, j, n in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(n):
            match[flat[j + k]] = aw[i + k]
    out = []
    for li, (w, line) in enumerate(zip(rows, lines)):
        onset = {}
        for wi in range(len(w)):
            x = match.get((li, wi))
            if x is None or x.get("score", 1) < 0.3:
                continue
            ts = syllable_onsets(x["form"], w.ipa.iloc[wi], x["start"], x["end"], x.get("chars") or [], LABELS)
            for s_i, t in enumerate(ts):
                onset[(wi, s_i)] = t
        out.append([position16(onset[(k.word, k.syl)], al["beats"], al["downbeats"])
                    if (k.word, k.syl) in onset else None for k in line.ks])
    return out


if __name__ == "__main__":
    run()
