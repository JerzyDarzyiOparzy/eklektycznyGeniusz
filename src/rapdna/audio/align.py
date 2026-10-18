"""Forced alignment of known lyrics (Genius) to the vocals: torchaudio MMS_FA (wav2vec2 with CTC alignment, no speech
recognition). The text of the whole song (all sections, choruses and guests included, since they are in the
recording), words from tokenize()."""
import json
import unicodedata

import pandas as pd

from rapdna import paths
from rapdna.audio import ALIGN
from rapdna.audio.signal import read

SR = 16000
CHUNK_S, CONTEXT_S = 30, 2  # wav2vec2 over a whole song does not fit in 6 GB, so emissions are computed in windows
_PL = str.maketrans("łŁ", "lL")


def romanize(word: str, labels: set[str]) -> str:
    """The MMS vocabulary is Latin without diacritics: ą → a, ł → l, ż → z."""
    w = unicodedata.normalize("NFKD", word.translate(_PL).lower().replace("’", "'"))
    return "".join(ch for ch in w if ch in labels)


def song_words(song_id: int) -> pd.DataFrame:
    w = pd.read_parquet(paths.PARQUET / "words.parquet", columns=["line_uid", "w", "form"])
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet", columns=["line_uid", "song_id", "section", "line", "text",
                                                                      "performers", "section_type"])
    lines = lines[lines.song_id == song_id]
    return (w.merge(lines, on="line_uid").sort_values(["section", "line", "w"]).reset_index(drop=True))


def emissions(wave, model, device):
    import torch

    n, step, ctx = wave.shape[1], CHUNK_S * SR, CONTEXT_S * SR
    out = []
    with torch.inference_mode():
        for s in range(0, n, step):
            a, b = max(0, s - ctx), min(n, s + step + ctx)
            em, _ = model(wave[:, a:b].to(device))
            fps = em.shape[1] / (b - a)  # frames per sample
            lo, hi = round((s - a) * fps), round((min(n, s + step) - a) * fps)
            out.append(em[0, lo:hi].cpu())
    return torch.cat(out)


def align(song_id: int, vocals, device: str = "cuda", words: pd.DataFrame | None = None) -> pd.DataFrame:
    """words: song words from outside the corpus (column form, in text order); by default from words.parquet."""
    import torch
    import torchaudio

    bundle = torchaudio.pipelines.MMS_FA
    labels = set(bundle.get_dict()) - {"-", "*"}
    words = song_words(song_id) if words is None else words.copy()
    words["token"] = [romanize(f, labels) for f in words.form]
    words = words[words.token.str.len() > 0].reset_index(drop=True)

    model = bundle.get_model(with_star=False).to(device)
    wave = torch.from_numpy(read(vocals, SR))
    em = emissions(wave, model, device)
    spans = bundle.get_aligner()(em, bundle.get_tokenizer()(list(words.token)))
    sec = wave.shape[1] / em.shape[0] / SR
    words["start"] = [sp[0].start * sec for sp in spans]
    words["end"] = [sp[-1].end * sec for sp in spans]
    words["score"] = [sum(t.score * (t.end - t.start) for t in sp) / sum(t.end - t.start for t in sp) for sp in spans]
    # characters in time: for splitting a word into syllables
    words["chars"] = [[(t.start * sec, t.end * sec) for t in sp] for sp in spans]
    return words


def save(song_id: int, words: pd.DataFrame, beats: list[float], downbeats: list[float]) -> None:
    ALIGN.mkdir(parents=True, exist_ok=True)
    (ALIGN / f"{song_id}.json").write_text(json.dumps({
        "song_id": song_id, "beats": beats, "downbeats": downbeats,
        "words": words.to_dict("records"),  # „chars”: time of every letter of the romanized spelling (for syllables)
    }, ensure_ascii=False), encoding="utf-8")
