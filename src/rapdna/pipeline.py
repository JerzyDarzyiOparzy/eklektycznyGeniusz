"""data/songs.jsonl → data/parquet/{lines,words,rhymes}.parquet: sections, lines, words with IPA and morphology, rhymes."""
from collections import defaultdict

import pandas as pd

from rapdna import paths
from rapdna.audio.overrides import load_overrides
from rapdna.ingest import album_year, load_config, load_songs
from rapdna.rhymes.density import Word
from rapdna.rhymes.hb_detect import candidates_section, thresholds
from rapdna.rhymes.hb import MODEL_FILE, RhymeModel, make_tail, train
from rapdna.rhymes.patterns import count_syllables
from rapdna.text.nlp import annotate, is_function_word
from rapdna.text.phonetics import Lexicon, context_english, is_english_line, polish_in_english_line, \
    spelled_acronym, tokenize
from rapdna.text.sections import attributed_to, parse_sections

SONG_DUP_SHARE = 0.6
RHYME_SECTIONS = {"verse", "chorus", "prechorus", "postchorus", "bridge", "intro", "outro", "other"}


def shingles(text: str, n: int = 5) -> set[tuple[str, ...]]:
    words = [w.lower() for w in tokenize(text)]
    return {tuple(words[i:i + n]) for i in range(len(words) - n + 1)}


def process(log=print) -> dict[str, int]:
    songs = load_songs()
    # shorter songs first: a compilation of parts (e.g. „ŁAŃCUCH (wszystkie części)”) comes out as a duplicate
    songs.sort(key=lambda s: (s["artist"], s.get("release_date") or "", len(s["lyrics"])))

    aliases = {a["name"]: a.get("aliases", []) for a in load_config()["artists"]}
    lines, seen, seen_lines = [], defaultdict(set), defaultdict(set)
    for s in songs:
        sections = parse_sections(s["lyrics"], s["artist"], s["featured"], aliases.get(s["artist"], []))
        # a song made mostly of text already seen for this rapper (compilation, alternative version); compared on
        # 5-word shingles, because versions of the same text are often broken into lines differently
        keys = shingles(" ".join(ln for sec in sections for ln in sec.lines))
        song_dup = bool(keys) and len(keys & seen_lines[s["artist"]]) / len(keys) >= SONG_DUP_SHARE
        seen_lines[s["artist"]] |= keys
        for si, sec in enumerate(sections):
            dup = song_dup or sec.is_dup or sec.text_key in seen[s["artist"]]
            seen[s["artist"]].add(sec.text_key)
            for li, text in enumerate(sec.lines):
                lines.append({
                    "line_uid": f"{s['song_id']}:{si}:{li}",
                    "song_id": s["song_id"], "artist": s["artist"], "album": s["album"].strip(),
                    "year": album_year(s["song_id"]) or (int(s["release_date"][:4]) if s.get("release_date") else None),
                    "title": s["title"], "section": si, "section_type": sec.type,
                    "performers": "; ".join(sec.performers), "attributed": attributed_to(sec, s["artist"], aliases.get(s["artist"], [])),
                    "is_dup": dup, "line": li, "text": text,
                })
    lines_df = pd.DataFrame(lines)

    lex = Lexicon()
    tokens = {ln["line_uid"]: tokenize(ln["text"]) for ln in lines}
    lex.load({t for toks in tokens.values() for t in toks})
    english_lines = {uid for uid, toks in tokens.items() if is_english_line(toks)}
    # in Polish lines, words of both languages next to English ones („I'll be back”, „Frank Castle”), rules D, E, N
    context_en = set()
    for uid, toks in tokens.items():
        if uid in english_lines:
            continue
        base = [lex.lang.get(t.lower()) == "en" for t in toks]
        context_en |= {(uid, i) for i, (b, c) in enumerate(zip(base, context_english(toks, base))) if c and not b}
    lex.load_english({t for uid in english_lines for t in tokens[uid]} | {tokens[uid][i] for uid, i in context_en})
    log(f"vocabulary: {len(lex.ipa)} forms, from espeak: {sum(v == 'espeak' for v in lex.source.values())}, "
        f"English lines: {len(english_lines)}")

    ann = annotate(tokens, lex.lemma, log=log)
    heard = load_overrides()
    log(f"pronunciation heard in recordings: {len(heard)} words")
    words = []
    for uid, toks in tokens.items():
        for wi, (form, (lemma, pos, person, number)) in enumerate(zip(toks, ann[uid])):
            # in an English line, words hardly known in English are read as Polish (rule B, config/word_language.yaml)
            english = uid in english_lines and not polish_in_english_line(form) or (uid, wi) in context_en
            ipa = lex.ipa_en[form.lower()] if english else lex[form]
            ipa = spelled_acronym(form) or ipa
            lang = "en" if english else lex.lang.get(form.lower(), "pl")
            if (uid, wi) in heard:  # pronunciation settled from a recording (audio/overrides.py)
                ipa, lang = heard[uid, wi]["ipa"], heard[uid, wi]["lang"]
            words.append({
                "line_uid": uid, "w": wi, "form": form, "lemma": lemma, "pos": pos, "person": person, "number": number,
                "ipa": ipa, "lang": lang, "n_syll": count_syllables(ipa),
                "function": is_function_word(form, pos),
            })
    words_df = pd.DataFrame(words)

    paths.PARQUET.mkdir(parents=True, exist_ok=True)
    for name, df in (("lines", lines_df), ("words", words_df)):
        df.to_parquet(paths.PARQUET / f"{name}.parquet", index=False)
    return {"lines": len(lines_df), "words": len(words_df), **detect_rhymes(lines_df, words_df, log=log)}


def section_words(lines_df: pd.DataFrame, words_df: pd.DataFrame):
    """(song_id, section, artist, uids, lines as lists of Word) for every section, lines in order."""
    by_line = {uid: g for uid, g in words_df.groupby("line_uid", sort=False)}
    for (song_id, sec), g in lines_df.sort_values(["song_id", "section", "line"]).groupby(["song_id", "section"], sort=False):
        uids = list(g.line_uid)
        yield song_id, sec, g.artist.iloc[0], uids, [
            [Word(r.form, r.ipa, r.function) for r in by_line[u].itertuples()] if u in by_line else [] for u in uids
        ]


def training_tails(lines_df: pd.DataFrame, words_df: pd.DataFrame) -> list:
    """Line tails in every section (all performers, no repeats): training data for the rhyme models."""
    nodup = lines_df[~lines_df.is_dup]
    return [[make_tail([(w.form, w.ipa) for w in ln]) for ln in sec] for *_, sec in section_words(nodup, words_df)]


def detect_rhymes(lines_df: pd.DataFrame | None = None, words_df: pd.DataFrame | None = None, train_model: bool = True,
                  log=print) -> dict[str, int]:
    """Hirjee & Brown baseline: trains the model on the whole corpus (all lines without repeats), scores candidates in
    the rapper's sections and keeps rhymes above the thresholds in config/thresholds.yaml (→ rhymes_hb.parquet, for
    comparison only). Then the rhymes used in the statistics (`rhymes_rules`)."""
    if lines_df is None:
        lines_df = pd.read_parquet(paths.PARQUET / "lines.parquet")
        words_df = pd.read_parquet(paths.PARQUET / "words.parquet")
    nodup = lines_df[~lines_df.is_dup]
    if train_model or not MODEL_FILE.exists():
        log("rhyme model (Hirjee & Brown):")
        model = train(training_tails(lines_df, words_df), log=log)
    else:
        model = RhymeModel.load()

    th = thresholds()
    eligible = nodup[nodup.attributed & nodup.section_type.isin(RHYME_SECTIONS)]
    cands = []
    for song_id, sec, artist, uids, sec_lines in section_words(eligible, words_df):
        for r in candidates_section(sec_lines, model):
            cands.append({
                "song_id": song_id, "artist": artist, "kind": r.kind, "type": r.type,
                "line_a": uids[r.line_a], "word_a": r.word_a, "line_b": uids[r.line_b], "word_b": r.word_b,
                "syllables": r.syllables, "score": r.score,
            })
    cand_df = pd.DataFrame(cands)
    # the same pair of lines repeated in a song (e.g. a two-line hook, also in reverse order) counts once
    text = lines_df.set_index("line_uid").text.str.lower()
    a = cand_df.line_a.map(text) + "#" + cand_df.word_a.astype(str)
    b = cand_df.line_b.map(text) + "#" + cand_df.word_b.astype(str)
    cand_df["_key"] = [tuple(sorted(p)) for p in zip(a, b)]
    cand_df = cand_df.drop_duplicates(["artist", "_key"]).drop(columns="_key")

    end = cand_df[(cand_df.kind == "end") & (cand_df.score >= th["tau_end"])]
    end = end.sort_values("score", ascending=False).drop_duplicates("line_b")
    internal = cand_df[(cand_df.kind == "internal") & (cand_df.score >= th["tau_internal"])]
    rhymes_df = pd.concat([end, internal], ignore_index=True)
    rhymes_df["validated"] = bool(th.get("calibrated"))

    cand_df.to_parquet(paths.PARQUET / "candidates.parquet", index=False)
    rhymes_df.to_parquet(paths.PARQUET / "rhymes_hb.parquet", index=False)
    return {"candidates": len(cand_df), "rhymes_hb": len(rhymes_df), **rhymes_rules(lines_df, words_df, log=log)}


def rhymes_rules(lines_df: pd.DataFrame, words_df: pd.DataFrame, log=print) -> dict[str, int]:
    """Rhymes used in the statistics → data/parquet/rhymes.parquet. End rhymes: shared vowel tail (`rhymes/end.py`);
    internal rhymes: the rule-based ruler (docs/en/methodology.md). All end-rhyme pairs stay (AABB, ABAB…
    layouts); `best` marks the best partner of each line."""
    from rapdna.rhymes.end import end_rhymes
    from rapdna.rhymes.match import thresholds as th_r
    from rapdna.rhymes.ruler_corpus import detect

    df = detect(lines_df, words_df, log=log)
    df[df.kind == "end"].to_parquet(paths.PARQUET / "rhymes_end_r.parquet", index=False)
    end = end_rhymes(lines_df, words_df, log=log).sort_values("score", ascending=False)
    end = end.assign(best=~end.duplicated("line_b"))
    out = pd.concat([end, df[df.kind != "end"].assign(best=False)], ignore_index=True)
    out["validated"] = bool(th_r().get("calibrated"))
    out.to_parquet(paths.PARQUET / "rhymes.parquet", index=False)
    return {"rhymes": len(out), **{f"rhymes_{k}": int(v) for k, v in out.anchor.value_counts().items()}}
