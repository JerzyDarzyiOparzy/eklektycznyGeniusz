"""Enjambment.

Validation (gold set): the spaCy dependency-parser variant had precision 2/64: Genius lyrics have almost
no punctuation and the parser links words across the line boundary blindly. So the statistic uses the „hanging end”
rule (`hanging_end`): the line ends with a preposition or a conjunction, so the sentence has to run on.
`detect` (the parser) stays for comparison.

Parser variant (plan: spaCy dependency parser). A pair of neighbouring lines goes to the parser as one sequence;
enjambment = the last word of the line „hangs”: it depends (by a phrase-internal relation) on one of the first words
of the next line, e.g. a preposition „wraca z / tacą”, a conjunction „jagód i / brzoskwiń”, an adjective before a
noun. Only this narrow, safer case is taken. Results are cached on disk.
"""
import json

from rapdna import paths

CACHE = paths.DATA / "enjambment_cache.json"
BINDING = {"nsubj", "nsubj:pass", "obj", "iobj", "obl", "obl:arg", "obl:agent", "nmod", "nmod:poss", "amod", "det",
           "det:poss", "det:numgov", "case", "nummod", "nummod:gov", "aux", "aux:pass", "cop", "fixed", "flat",
           "compound", "xcomp", "advmod", "mark", "acl", "expl:pv", "cc", "flat:name"}
HEAD_WINDOW = 3  # the head of the line's last word must be among the first words of the next line


def detect(pairs: dict[str, tuple[list[str], list[str]]], log=print) -> dict[str, bool]:
    """key → (words of line i, words of line i+1); returns key → whether line i runs on into i+1."""
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    keys = {k: " ".join(a).lower() + " || " + " ".join(b).lower() for k, (a, b) in pairs.items()}
    todo = sorted({v for k, v in keys.items() if v not in cache and pairs[k][0] and pairs[k][1]})
    if todo:
        import spacy
        from spacy.tokens import Doc

        log(f"spaCy parser: {len(todo)} line pairs…")
        nlp = spacy.load("pl_core_news_lg", exclude=["ner"])
        def docs():
            for t in todo:
                a, b = t.split(" || ")
                words = a.split(" ") + b.split(" ")
                yield Doc(nlp.vocab, words=words, sent_starts=[True] + [False] * (len(words) - 1))
        for t, doc in zip(todo, nlp.pipe(docs(), batch_size=256)):
            n1 = len(t.split(" || ")[0].split(" "))
            last = doc[n1 - 1]
            cache[t] = bool(last.dep_ in BINDING and n1 <= last.head.i < n1 + HEAD_WINDOW)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {k: bool(cache.get(v, False)) for k, v in keys.items()}


HANGING_POS = {"ADP", "CCONJ", "SCONJ"}


def hanging_end(last_form: str, last_pos: str) -> bool:
    """The line ends with a word that cannot close a phrase (preposition, conjunction: „z”, „i”, „że”, „bo”)."""
    return last_pos in HANGING_POS and last_form.lower() not in {"jak", "co", "ej"}
