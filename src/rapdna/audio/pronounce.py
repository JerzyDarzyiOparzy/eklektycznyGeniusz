"""Pronunciation from a recording: which reading of a word (Polish / English)
fits the vocals better. CTC likelihood (summed over all paths) of the romanized spelling in the word's window from the
alignment; the same stretch of audio for both spellings, so the scores are comparable. The spellings are generated
from the IPA of both readings (respell)."""
import json
import re

import pandas as pd
import torch
import torch.nn.functional as F
from wordfreq import zipf_frequency

from rapdna import paths
from rapdna.audio import ALIGN
from rapdna.audio.align import romanize
from rapdna.audio.overrides import PRON

PAD_S = 0.15
LETTERS = set("abcdefghijklmnopqrstuvwxyz'")

# IPA (espeak notation after _en_to_pl) → Latin letters in Polish spelling without diacritics, like the alignment text
_RESPELL = [
    # diphthongs as vowels („stounz”, „hejw” → „heiw”): „w” and „ł” mean different things in the two languages; the
    # model read „stownz” as Polish „stołnz” and picked the worse spelling (Stones, hole in the pilot)
    ("ɔw", "ou"), ("aw", "au"), ("ɛj", "ei"), ("aj", "ai"), ("ɔj", "oi"),
    ("tʃ", "cz"), ("dʒ", "dz"), ("tɕ", "c"), ("dʑ", "dz"), ("ts", "c"), ("ʃ", "sz"), ("ʂ", "sz"), ("ʒ", "z"),
    ("ʐ", "z"), ("ɕ", "s"), ("ʑ", "z"), ("ɛ̃", "en"), ("ɔ̃", "on"), ("ɨ", "y"), ("ɛ", "e"), ("ɔ", "o"), ("ɡ", "g"),
    ("x", "ch"), ("ç", "ch"), ("ɲ", "n"), ("ŋ", "n"), ("v", "w"), ("ɟ", "g"), ("ʲi", "i"), ("ʲ", "i"),
]


def respell(ipa: str) -> str:
    s = re.sub("[ˈˌː ]", "", ipa)
    for a, b in _RESPELL:
        s = s.replace(a, b)
    return re.sub("[^a-z]", "", s)


class Scorer:
    def __init__(self, vocals, device: str = "cuda"):
        import torchaudio

        from rapdna.audio.align import SR, emissions
        from rapdna.audio.signal import read

        bundle = torchaudio.pipelines.MMS_FA
        self.dictionary = bundle.get_dict()
        model = bundle.get_model(with_star=False).to(device)
        wave = torch.from_numpy(read(vocals, SR))
        self.em = emissions(wave, model, device).float().log_softmax(-1)
        self.sec = wave.shape[1] / self.em.shape[0] / SR

    def score(self, spelling: str, start: float, end: float) -> float:
        a = max(0, int((start - PAD_S) / self.sec))
        b = min(self.em.shape[0], int((end + PAD_S) / self.sec) + 1)
        lp = self.em[a:b]
        target = torch.tensor([[self.dictionary[c] for c in spelling]])
        loss = F.ctc_loss(lp[:, None], target, torch.tensor([lp.shape[0]]), torch.tensor([target.shape[1]]),
                          blank=self.dictionary["-"], reduction="sum", zero_infinity=True)
        return -float(loss)

    def choose(self, candidates: dict[str, str], start: float, end: float) -> tuple[str, dict[str, float]]:
        scores = {k: self.score(v, start, end) for k, v in candidates.items()}
        return max(scores, key=scores.get), scores


def readings(forms: set[str]) -> dict[str, dict[str, str]]:
    """For every word, the Polish reading (dictionary or espeak-pl) and the English one (hybrid or espeak en-us)."""
    from rapdna.text.phonetics import (ESPEAK_CACHE, _en_to_pl, english_stem, penultimate_stress, run_espeak)

    forms = {f.lower() for f in forms}
    cache = json.loads(ESPEAK_CACHE.read_text(encoding="utf-8")) if ESPEAK_CACHE.exists() else {}
    d = pd.read_parquet(paths.PHONETIC_DICT, filters=[("word", "in", sorted(forms))])
    pl = dict(zip(d.word, d.ipa))
    stems = {f: english_stem(f) for f in forms}
    need = {("pl", f) for f in forms if f not in pl} | {("en-us", st[0] if st else f) for f, st in stems.items()}
    for voice in ("pl", "en-us"):
        todo = sorted(w for v, w in need if v == voice and f"{voice}:{w}" not in cache)
        for w, ipa in zip(todo, run_espeak(todo, voice)):
            cache[f"{voice}:{w}"] = ipa
    ESPEAK_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    out = {}
    for f in forms:
        st = stems[f]
        en = (penultimate_stress(_en_to_pl(cache[f"en-us:{st[0]}"], st[0]) + st[1]) if st
              else _en_to_pl(cache[f"en-us:{f}"], f))
        out[f] = {"pl": pl.get(f) or cache[f"pl:{f}"], "en": en}
    return out


def ambiguous(form: str, lang: str) -> bool:
    """Candidates to decide: a word known in English or a hybrid, except common Polish words."""
    from rapdna.text.phonetics import LANG, english_stem

    w = form.lower()
    if lang == "pl" and zipf_frequency(w, "pl") >= LANG["c_max_pl"]:
        return False
    return lang == "en" or zipf_frequency(w, "en") >= 2.0 or english_stem(w) is not None


def decide(song_id: int, scorer: Scorer, performer: str | None = None) -> list[dict]:
    """Decisions for words with two different spellings in an aligned song → data/audio/pron/<song_id>.candidates.json."""
    from rapdna.text.phonetics import mostly_english

    words = json.loads((ALIGN / f"{song_id}.json").read_text(encoding="utf-8"))["words"]
    cur = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["line_uid", "w", "lang", "ipa"])
    cur = cur[cur.line_uid.isin({w["line_uid"] for w in words})].set_index(["line_uid", "w"])
    words = [w for w in words if (performer is None or w["performers"] == performer)
             and ambiguous(w["form"], cur.loc[(w["line_uid"], w["w"]), "lang"])]
    read = readings({w["form"] for w in words})
    out = []
    for w in words:
        r = read[w["form"].lower()]
        cand = {lang: respell(ipa) for lang, ipa in r.items()}
        if cand["pl"] == cand["en"] or not all(cand.values()):
            continue
        pick, s = scorer.choose(cand, w["start"], w["end"])
        if pick == "pl" and cand["pl"] == romanize(w["form"], LETTERS) and mostly_english(w["form"], 0):
            # the Polish spelling is literally the English one („stones”, „glory”): the model knows English and reads
            # it as English, so its win says nothing about a Polish reading; the rule reading stays
            continue
        out.append({"line_uid": w["line_uid"], "w": w["w"], "form": w["form"], "lang": pick, "ipa": r[pick],
                    "rules_lang": cur.loc[(w["line_uid"], w["w"]), "lang"], "spell": cand, "score": s,
                    "margin": abs(s["pl"] - s["en"]), "align_score": w["score"]})
    PRON.mkdir(parents=True, exist_ok=True)
    (PRON / f"{song_id}.candidates.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out
