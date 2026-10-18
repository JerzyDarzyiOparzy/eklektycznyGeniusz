"""Lemmas, parts of speech and grammatical person (spaCy pl_core_news_lg), and function words.

spaCy gets our own tokens (a Doc built from ready words), so its output aligns 1:1 with the words in
words.parquet. Results are cached on disk by line text, because a pass over the corpus takes several minutes.
"""
import json

from rapdna import paths

FUNCTION_POS = {"ADP", "CCONJ", "SCONJ", "PART", "PRON", "AUX", "DET", "INTJ"}

# Polish function words (prepositions, conjunctions, pronouns, auxiliaries, particles)
FUNCTION_WORDS = set("""
a aby albo ale ani aż bez bo by byle był była było były być chociaż choć co czy dla do dziś gdy gdzie go
i ich im ja jak jako je jego jej jest jeszcze jestem jesteś jeśli już ją każdy kiedy kto która które który
lub ma mam mi mnie mną mu my na nad nam nas nawet nic nie niech nim no o od on ona one oni ono po pod
przez przy się sobie są ta tak tam te tego tej ten to tobie toba tu tuż ty tylko tym u w we wy z za ze
że żeby ci cię ciebie tę tych też bym byś byłem byłam jakby albo oraz lecz więc zaś czyli by
""".split())

NLP_CACHE = paths.DATA / "nlp_cache.json"


def is_function_word(form: str, pos: str | None = None) -> bool:
    if form.lower() in FUNCTION_WORDS:
        return True
    return pos in FUNCTION_POS if pos else False


def annotate(lines: dict[str, list[str]], dict_lemma: dict[str, str], log=print) -> dict[str, list[tuple]]:
    """line uid → (lemma, pos, person, number) for every token."""
    cache: dict[str, list] = json.loads(NLP_CACHE.read_text(encoding="utf-8")) if NLP_CACHE.exists() else {}
    keys = {uid: " ".join(t.lower() for t in toks) for uid, toks in lines.items()}
    # entries from an older cache version (without grammatical number) are computed again
    todo = sorted({k for k in keys.values() if k and (k not in cache or (cache[k] and len(cache[k][0]) < 4))})
    if todo:
        import spacy
        from spacy.tokens import Doc

        log(f"spaCy: {len(todo)} new lines…")
        nlp = spacy.load("pl_core_news_lg", exclude=["parser", "ner"])
        docs = (Doc(nlp.vocab, words=k.split(" ")) for k in todo)
        for k, doc in zip(todo, nlp.pipe(docs, batch_size=512)):
            cache[k] = [[t.lemma_.split(" ")[0].lower(), t.pos_, "".join(t.morph.get("Person")),
                         "".join(t.morph.get("Number"))] for t in doc]
        NLP_CACHE.parent.mkdir(parents=True, exist_ok=True)
        NLP_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    out = {}
    for uid, toks in lines.items():
        ann = cache.get(keys[uid], [])
        if len(ann) != len(toks):
            ann = [["", "", "", ""]] * len(toks)
        rows = []
        for form, (lemma, pos, person, number) in zip(toks, ann):
            f = form.lower()
            # spaCy leaves unknown forms unchanged; then take the lemma from the phonetic dictionary (plWordNet),
            # but only for content words and lower-case lemmas („lecz” ≠ „leczo”, „na” ≠ „Na”)
            fallback = dict_lemma.get(f, "")
            if ((not lemma or lemma == f) and fallback and fallback.islower()
                    and not is_function_word(f, pos)):
                lemma = fallback
            rows.append((lemma or f, pos, person, number))
        out[uid] = rows
    return out
