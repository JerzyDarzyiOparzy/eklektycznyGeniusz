"""Client for the official Genius API (api.genius.com): metadata only, no lyrics."""
import json
import os
import time

import requests
from dotenv import load_dotenv

from rapdna import paths

API = "https://api.genius.com"
CACHE = paths.DATA / "api_cache"


class GeniusAPI:
    def __init__(self, token: str | None = None, delay: float = 0.5):
        load_dotenv(paths.ROOT / ".env")
        token = token or os.environ.get("GENIUS_TOKEN", "").strip().strip('"')
        if not token:
            raise RuntimeError("GENIUS_TOKEN is missing in .env")
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"
        self.delay = delay
        CACHE.mkdir(parents=True, exist_ok=True)

    def _get(self, endpoint: str, **params) -> dict:
        key = endpoint.strip("/").replace("/", "_") + "".join(f"_{k}-{v}" for k, v in sorted(params.items()))
        cached = CACHE / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
        time.sleep(self.delay)
        r = self.session.get(f"{API}{endpoint}", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()["response"]
        cached.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def search(self, query: str) -> list[dict]:
        """Song hits for a free-text query (cache file names cannot contain characters such as „?”)."""
        q = " ".join("".join(ch if ch.isalnum() else " " for ch in query).split())
        return [h["result"] for h in self._get("/search", q=q)["hits"]]

    def search_artist(self, name: str) -> list[dict]:
        """Artist candidates for a name (unique primary artists among the search hits)."""
        seen = {}
        for r in self.search(name):
            a = r["primary_artist"]
            seen.setdefault(a["id"], {"id": a["id"], "name": a["name"], "url": a["url"]})
        return list(seen.values())

    def artist_songs(self, artist_id: int) -> list[dict]:
        """All songs of an artist (pages of 50)."""
        songs, page = [], 1
        while page:
            data = self._get(f"/artists/{artist_id}/songs", per_page=50, page=page, sort="title")
            songs.extend(data["songs"])
            page = data.get("next_page")
        return songs

    def song(self, song_id: int) -> dict:
        return self._get(f"/songs/{song_id}", text_format="plain")["song"]

    def referents(self, song_id: int) -> list[dict]:
        """Fan annotations of song fragments (interpretations, not facts) with their vote counts."""
        out, page = [], 1
        while page:
            data = self._get("/referents", song_id=song_id, text_format="plain", per_page=50, page=page)
            out.extend(data["referents"])
            page = page + 1 if len(data["referents"]) == 50 else None
        return out


def cached_song(song_id: int) -> dict | None:
    """Song details from the API cache, without a request (None when the song was never fetched)."""
    f = CACHE / f"songs_{song_id}_text_format-plain.json"
    return json.loads(f.read_text(encoding="utf-8"))["song"] if f.exists() else None
