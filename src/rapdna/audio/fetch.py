"""Downloading recordings from YouTube (yt-dlp). Video choice: first the „<rapper> - Topic” channel (the album version,
without music-video intros); live versions are skipped. See docs/en/roadmap.md."""
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from rapdna.audio import RAW

_LIVE = re.compile(r"\b(live|koncert|concert|zapis)\b", re.I)


def _yt_dlp() -> str:
    return str(Path(sys.executable).with_name("yt-dlp.exe" if sys.platform == "win32" else "yt-dlp"))


def search(query: str, n: int = 8) -> list[dict]:
    out = subprocess.run([_yt_dlp(), f"ytsearch{n}:{query}", "--flat-playlist", "-J"],
                         capture_output=True, check=True).stdout.decode("utf-8")
    return [{"id": e["id"], "title": e.get("title") or "", "duration": e.get("duration"),
             "channel": e.get("channel") or ""} for e in json.loads(out).get("entries", [])]


def _norm(s: str) -> str:
    """Without diacritics and punctuation („Jak nagrać 1szą płytę?” = „Jak nagrac 1sza plyte”)."""
    s = unicodedata.normalize("NFKD", s.replace("ł", "l").replace("Ł", "L").lower())
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s.encode("ascii", "ignore").decode()).split())


def choose(entries: list[dict], artist: str, title: str) -> dict | None:
    """A Topic channel video with the song title, then any video with the title; no live versions, nothing over 15 min."""
    ok = [e for e in entries if not _LIVE.search(e["title"]) and (e["duration"] or 0) < 900
          and _norm(title) in _norm(e["title"])]
    topic = [e for e in ok if _norm(e["channel"]) == _norm(f"{artist} - topic")]
    return (topic or ok or [None])[0]


def download(song_id: int, artist: str, title: str, log=print) -> Path | None:
    dst = RAW / f"{song_id}.wav"
    if dst.exists():
        return dst
    pick = choose(search(f"{artist} {title}"), artist, title)
    if pick is None:
        log(f"{song_id}: no matching recording for „{artist} - {title}”")
        return None
    log(f"{song_id}: {pick['title']} [{pick['channel']}, {pick['duration']} s]")
    RAW.mkdir(parents=True, exist_ok=True)
    subprocess.run([_yt_dlp(), "-q", "-f", "bestaudio", "-x", "--audio-format", "wav",
                    "-o", str(RAW / f"{song_id}.%(ext)s"), f"https://www.youtube.com/watch?v={pick['id']}"], check=True)
    (RAW / f"{song_id}.json").write_text(json.dumps(pick, ensure_ascii=False), encoding="utf-8")
    return dst
