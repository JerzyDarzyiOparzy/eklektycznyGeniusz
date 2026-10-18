"""Pronunciation settled from recordings (audio/pronounce.py) → IPA corrections in the pipeline. No torch here: the
text pipeline runs without the audio dependencies and without downloaded recordings."""
import json

from rapdna.audio import AUDIO

PRON = AUDIO / "pron"  # <song_id>.candidates.json: decisions from the recording; <song_id>.json: approved after listening
MIN_MARGIN = 2.0  # the smallest likelihood gap in the pilot check was 3.0; below the threshold the rule reading stays


def load_overrides() -> dict[tuple[str, int], dict]:
    """Approved files only: in the pilot 3 of 10 decisions looked wrong (rappers mix pronunciations and there are
    only two spellings to choose from), so decisions from a recording need a listening check."""
    out = {}
    for f in sorted(PRON.glob("*[0-9].json")) if PRON.exists() else []:
        for d in json.loads(f.read_text(encoding="utf-8")):
            if d["margin"] >= MIN_MARGIN:
                out[d["line_uid"], d["w"]] = {"ipa": d["ipa"], "lang": d["lang"]}
    return out
