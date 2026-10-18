"""Lyrics from song pages on genius.com.

One request every few seconds, every page fetched once (HTML cache in data/raw_html), no attempt to get around
anti-bot protection. When a page is unavailable, the lyrics can be saved by hand to data/lyrics/<song_id>.txt
(with section headers) and are used instead of the HTML.
"""
import random
import re
import time

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

from rapdna import paths

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}


class LyricsUnavailable(Exception):
    pass


class GeniusScraper:
    def __init__(self, min_delay: float = 3.0, max_delay: float = 5.0):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.min_delay, self.max_delay = min_delay, max_delay
        paths.RAW_HTML.mkdir(parents=True, exist_ok=True)
        paths.LYRICS.mkdir(parents=True, exist_ok=True)

    def html(self, song_id: int, url: str) -> str:
        cached = paths.RAW_HTML / f"{song_id}.html"
        if cached.exists():
            return cached.read_text(encoding="utf-8")
        time.sleep(random.uniform(self.min_delay, self.max_delay))
        r = self.session.get(url, timeout=30)
        if r.status_code != 200:
            raise LyricsUnavailable(f"{url}: HTTP {r.status_code}")
        cached.write_text(r.text, encoding="utf-8")
        return r.text

    def lyrics(self, song_id: int, url: str) -> str:
        manual = paths.LYRICS / f"{song_id}.txt"
        if manual.exists():
            return manual.read_text(encoding="utf-8")
        return extract_lyrics(self.html(song_id, url))


def _container_text(node: Tag) -> str:
    """Text of a lyrics container with <br> as newlines, skipping elements excluded from selection."""
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name == "br":
            parts.append("\n")
        elif child.get("data-exclude-from-selection") == "true":
            continue
        else:
            parts.append(_container_text(child))
    return "".join(parts)


def extract_lyrics(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select('div[data-lyrics-container="true"]')
    if not containers:
        raise LyricsUnavailable("no lyrics container on the page")
    text = "\n".join(_container_text(c) for c in containers)
    return clean_lyrics(text)


def clean_lyrics(text: str) -> str:
    # page header pasted before the lyrics: "12 ContributorsTitle Lyrics" plus an optional description
    first_section = re.search(r"^\[", text, flags=re.M)
    if first_section and re.search(r"Contributors|Lyrics", text[: first_section.start()]):
        text = text[first_section.start():]
    text = re.sub(r"\d*Embed$", "", text.strip())
    text = text.replace("You might also like", "")
    lines = [ln.strip() for ln in text.splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
