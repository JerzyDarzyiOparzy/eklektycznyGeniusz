"""Reference rhyme annotations: songs with every rhymed fragment marked by hand and grouped by colour.

`data/rhyme_annotations/annotations.json` (not in the repository, it contains full lyrics):
    {song title: {"song_id": int,
                  "rows": [{"text": str, "section": int}, ...],       one entry per line
                  "marks": [{"row": int, "i": int, "j": int, "group": str}, ...]}}
`i`, `j` are a character range in the line text; marks with the same `group` rhyme with each other.
`songs.json` maps the song titles to Genius ids.
"""
import json

from rapdna import paths
from rapdna.genius.scrape import extract_lyrics
from rapdna.text.sections import parse_sections

DIR = paths.DATA / "rhyme_annotations"
FILE = DIR / "annotations.json"
SONGS = DIR / "songs.json"


def load() -> dict:
    return json.loads(FILE.read_text(encoding="utf-8"))


def genius_lines(song_id: int) -> list[dict]:
    """Lines of a song as on Genius, with their section."""
    html = (paths.RAW_HTML / f"{song_id}.html").read_text(encoding="utf-8")
    out = []
    for si, sec in enumerate(parse_sections(extract_lyrics(html), "", [])):
        for li, text in enumerate(sec.lines):
            out.append({"section": si, "line": li, "text": text, "header": sec.header, "type": sec.type})
    return out
