"""Rapper profile page: data from `stats/profile.py` plus short examples, injected into
`site/templates/profiles.html` → site/dna.html.

Only numbers and short fragments reach the page: the longest end rhymes (a few words each),
favourite phrases, producers, ad-libs and words outside dictionaries.
"""
import json
from collections import Counter

import pandas as pd

from rapdna import paths
from rapdna.ingest import load_config

TEMPLATE = paths.ROOT / "src" / "rapdna" / "site" / "templates" / "profiles.html"
OUT = paths.SITE / "dna.html"
STATS = paths.DATA / "stats"
ERA = {"1990s": "lata 90.", "2000s": "lata 2000.", "2010s": "lata 2010.", "2020s": "lata 2020."}

# features computed but left out of profiles, with the reason shown on the page
EXCLUDED = [
    {"label": "Anafory", "dimension": "Figury i powtórzenia", "key": "anaphoras_100",
     "why": "wykrywanie trafne, ale zależą od utworu: średnia rapera byłaby pewna dopiero przy ~180 utworach"},
    {"label": "Aliteracje", "dimension": "Figury i powtórzenia", "key": "alliterations_100",
     "why": "jak anafory: potrzeba ~330 utworów"},
    {"label": "Epifory", "dimension": "Figury i powtórzenia", "key": "epiphoras_100",
     "why": "zależą od utworu (~56 utworów na pewną średnią)"},
    {"label": "Wymienianie własnej ksywy", "dimension": "Treść", "key": "self_mentions_1000",
     "why": "zależy od utworu (~78 utworów na pewną średnią)"},
    {"label": "Zdrobnienia i zgrubienia", "dimension": "Język i słownictwo", "key": "diminutives_1000",
     "why": "metoda po końcówkach słów myli się w połowie przypadków (lotnisko, stanowisko) – potrzebny słownik"},
    {"label": "Rymy wewnętrzne", "dimension": "Rymy", "key": None,
     "why": "w opracowaniu: zgodność z ludźmi ok. 76% (pary wersów), poza profilem do decyzji"},
    {"label": "Tematy, perspektywa, odniesienia", "dimension": "Treść", "key": None,
     "why": "policzone dla raperów, czekają na test raper / utwór"},
    {"label": "Rytm, flow, głos", "dimension": "Wykonanie", "key": None,
     "why": "wymagają nagrań całego dorobku – odłożone"},
]


def _fragment(words: list, line, k_range, keep: int = 6) -> dict:
    """The end of a line (up to `keep` words) with the rhyme words marked: a short fragment, not the whole text."""
    hit = {line.ks[u].word for u in range(int(k_range[0]), int(k_range[1]) + 1)}
    start = max(0, min(min(hit), len(words) - keep))
    return {"cut": start > 0, "words": [[words[i][0], i in hit] for i in range(start, len(words))]}


def rhyme_examples(per_artist: int = 3) -> dict:
    """The longest end rhymes of each rapper, from different line pairs."""
    from rapdna.rhymes.match import build_line

    rh = pd.read_parquet(paths.PARQUET / "rhymes.parquet")
    end = rh[(rh.kind == "end") & rh.validated & rh.best].sort_values(["syllables", "score"], ascending=False)
    picks = end.groupby("artist").head(15)
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet").set_index("line_uid")
    w = pd.read_parquet(paths.PARQUET / "words.parquet")
    w = w[w.line_uid.isin(set(picks.line_a) | set(picks.line_b))].sort_values(["line_uid", "w"])
    by = {u: list(zip(g.form, g.ipa, g.lemma, g.pos)) for u, g in w.groupby("line_uid")}
    out = {}
    for artist, g in picks.groupby("artist"):
        ex, seen = [], set()
        for r in g.itertuples():
            ta, tb = lines.text[r.line_a].lower(), lines.text[r.line_b].lower()
            if ta in seen or tb in seen or r.line_a not in by or r.line_b not in by:
                continue
            seen |= {ta, tb}
            ex.append({"a": _fragment(by[r.line_a], build_line(by[r.line_a]), r.k_a),
                       "b": _fragment(by[r.line_b], build_line(by[r.line_b]), r.k_b),
                       "syllables": int(r.syllables), "type": r.type, "title": lines.title[r.line_b]})
            if len(ex) == per_artist:
                break
        out[artist] = {"rhymes": ex}
    return out


def _fragment_html(frag: dict) -> str:
    from html import escape

    words = " ".join(f"<mark>{escape(w)}</mark>" if hit else escape(w) for w, hit in frag["words"])
    return ("… " if frag["cut"] else "") + words


def _repeated(r: dict) -> bool:
    """A pair of nearly the same words (a repeated line with one word changed) is repetition, not a rhyme."""
    a = {w.lower() for w, _ in r["a"]["words"]}
    b = {w.lower() for w, _ in r["b"]["words"]}
    return len(a & b) / max(min(len(a), len(b)), 1) >= 0.5


def _content(phrase: str) -> bool:
    """At least half of the words carry meaning („prosto z mostu”, „a propos”), not „że ktoś mnie”."""
    from rapdna.text.nlp import is_function_word

    toks = phrase.split()
    return sum(not is_function_word(t) and t not in PRONOUNS for t in toks) >= len(toks) / 2


PRONOUNS = {"ktoś", "coś", "nikt", "nic", "mój", "moja", "moje", "twój", "twoja", "swój", "swoje", "jakiś", "taki"}


def extras() -> dict:
    phrases = pd.read_csv(STATS / "phrases.csv")
    surface = pd.read_csv(STATS / "surface_features.csv").set_index("artist")
    adlibs = pd.read_csv(STATS / "adlibs.csv")
    words = pd.read_csv(paths.DATA / "candidates" / "words_to_review.csv")
    rhymes = rhyme_examples(per_artist=12)
    out = {}
    for artist in surface.index:
        own = words[words.rappers.str.contains(artist, regex=False)]
        # words used only by this rapper
        own = own[own.rappers.str.count(";") == 0].head(8)
        producers = surface.loc[artist, "main_producers"]
        out[artist] = {
            "rhymes": [{"a": _fragment_html(r["a"]), "b": _fragment_html(r["b"]), "syllables": r["syllables"],
                        "title": r["title"]} for r in rhymes.get(artist, {}).get("rhymes", [])
                       if not _repeated(r)][:3],
            "phrases": [{"text": r.phrase, "songs": int(r.songs)}
                        for r in phrases[phrases.artist == artist].itertuples() if _content(r.phrase)][:5],
            "producers": producers if isinstance(producers, str) else "",
            "adlibs": [r.adlib for r in adlibs[adlibs.artist == artist].itertuples()
                       if ":" not in r.adlib and len(r.adlib.split()) <= 3][:6],
            "slang": list(own.form),
        }
    return out


def build() -> str:
    data = json.loads((STATS / "profiles.json").read_text(encoding="utf-8"))
    icc = pd.read_csv(STATS / "reliability.csv").set_index("feature").icc
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    own = lines[lines.attributed & ~lines.is_dup]
    tech = pd.read_csv(STATS / "artists.csv").set_index("artist")
    era = {a["name"]: ERA.get(a.get("era"), "") for a in load_config()["artists"]}
    data["meta"] = {a: {"era": era.get(a, ""), "albums": int(own[own.artist == a].album.nunique()),
                        "words": int(tech.loc[a, "words"]) if a in tech.index else None} for a in data["profiles"]}
    data["corpus"] = {"artists": data["artists"], "songs": int(own.song_id.nunique()), "words": int(tech.words.sum())}
    data["extras"] = extras()
    data["excluded"] = [{**x, "icc": float(icc[x["key"]]) if x["key"] in icc.index else None} for x in EXCLUDED]
    html = TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", json.dumps(data, ensure_ascii=False))
    paths.SITE.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return str(OUT)


if __name__ == "__main__":
    print(build())
