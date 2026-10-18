"""Metadata (Genius API) and lyrics (Genius pages) for the rappers listed in config/artists.yaml."""
import json
import re
from collections import Counter

import yaml

from rapdna import paths
from rapdna.genius.api import GeniusAPI, cached_song
from rapdna.genius.scrape import GeniusScraper, LyricsUnavailable

ARTISTS_FILE = paths.CONFIG / "artists.yaml"
SONGS_FILE = paths.DATA / "songs.jsonl"


def load_config() -> dict:
    return yaml.safe_load(ARTISTS_FILE.read_text(encoding="utf-8"))


def save_genius_ids(ids: dict[str, int]) -> None:
    """Fill in `genius_id: null` under `- name: X`, keeping the comments of the file."""
    lines = ARTISTS_FILE.read_text(encoding="utf-8").splitlines()
    current = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("- name:"):
            current = yaml.safe_load(stripped[len("- name:"):])
        elif stripped == "genius_id: null" and current in ids:
            lines[i] = ln.replace("null", str(ids[current]))
    ARTISTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_ids(api: GeniusAPI) -> list[tuple[str, int | None, list[dict]]]:
    """Fill in genius_id where the name matches exactly; return the candidates for ambiguous names."""
    report, ids = [], {}
    for a in load_config()["artists"]:
        if a.get("genius_id"):
            continue
        cands = api.search_artist(a["name"])
        exact = [c for c in cands if c["name"].casefold() == a["name"].casefold()]
        if len(exact) == 1:
            ids[a["name"]] = exact[0]["id"]
        report.append((a["name"], ids.get(a["name"]), cands))
    save_genius_ids(ids)
    return report


def own_songs(api: GeniusAPI, artist_id: int) -> list[dict]:
    """Songs where the rapper is the primary artist, with details (album, date, guests)."""
    listing = [s for s in api.artist_songs(artist_id) if s["primary_artist"]["id"] == artist_id]
    return [api.song(s["id"]) for s in listing]


def album_summary(songs: list[dict]) -> list[tuple[str, int]]:
    c = Counter((s.get("album") or {}).get("name", "(no album)") for s in songs)
    return c.most_common()


def fetch_artist(api: GeniusAPI, scraper: GeniusScraper, artist: dict, log=print) -> int:
    """Fetch the lyrics of the albums listed in the config and append them to data/songs.jsonl."""
    if not artist.get("albums"):
        raise ValueError(f"{artist['name']}: no album list in config/artists.yaml (see `rapdna albums`)")
    wanted = {a.strip().casefold() for a in artist["albums"]}
    done = existing_song_ids()
    n = 0
    with SONGS_FILE.open("a", encoding="utf-8") as out:
        for s in own_songs(api, artist["genius_id"]):
            album = (s.get("album") or {}).get("name", "")
            if album.strip().casefold() not in wanted or s["id"] in done:
                continue
            try:
                lyrics = scraper.lyrics(s["id"], s["url"])
            except LyricsUnavailable as e:
                log(f"  skipped {s['full_title']}: {e}")
                continue
            rec = {
                "song_id": s["id"],
                "artist": artist["name"],
                "artist_id": artist["genius_id"],
                "title": s["title"],
                "album": album,
                "release_date": s.get("release_date"),
                "featured": [f["name"] for f in s.get("featured_artists", [])],
                "url": s["url"],
                "lyrics": lyrics,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n += 1
            log(f"  {album}: {s['title']}")
    return n


def existing_song_ids() -> set[int]:
    if not SONGS_FILE.exists():
        return set()
    return {json.loads(ln)["song_id"] for ln in SONGS_FILE.open(encoding="utf-8")}


def load_songs() -> list[dict]:
    """Fetched songs without the ones the config excludes (`exclude`: live versions, musicals and the like)
    and without rappers marked `excluded` (fetched, but below the selection criteria)."""
    cfg = load_config()["artists"]
    excluded = {(a["name"], t.casefold()) for a in cfg for t in a.get("exclude", [])}
    dropped = {a["name"] for a in cfg if a.get("excluded")}
    songs = []
    for ln in SONGS_FILE.open(encoding="utf-8"):
        try:
            s = json.loads(ln)
        except json.JSONDecodeError:  # line still being written by `fetch`
            continue
        if (s["artist"], s["title"].casefold()) not in excluded and s["artist"] not in dropped:
            songs.append(s)
    return songs


def album_year(song_id: int) -> int | None:
    """Album release year from the cached song details (Genius: album.release_date_for_display)."""
    song = cached_song(song_id)
    album = (song or {}).get("album") or {}
    m = re.search(r"(?:19|20)\d{2}", album.get("release_date_for_display") or "")
    return int(m.group(0)) if m else None
