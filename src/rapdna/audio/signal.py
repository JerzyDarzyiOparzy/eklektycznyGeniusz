"""Signal: reading and writing through ffmpeg (no soundfile), vocals from Demucs (htdemucs), beats and bars from beat_this."""
import subprocess
import wave
from pathlib import Path

import numpy as np

from rapdna.audio import VOCALS


def read(path: Path, sr: int, mono: bool = True) -> np.ndarray:
    """File → float32 (channels, samples) at the given sample rate."""
    ch = 1 if mono else 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", str(ch), "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch).T.copy()


def write(path: Path, x: np.ndarray, sr: int) -> None:
    """(channels, samples) float → 16-bit WAV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").T
    with wave.open(str(path), "wb") as f:
        f.setnchannels(pcm.shape[1])
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


def separate_vocals(src: Path, song_id: int, device: str = "cuda") -> Path:
    dst = VOCALS / f"{song_id}.wav"
    if dst.exists():
        return dst
    import torch
    from demucs.apply import apply_model
    from demucs.pretrained import get_model

    model = get_model("htdemucs")
    x = torch.from_numpy(read(src, model.samplerate, mono=False))
    ref = x.mean(0)
    x = (x - ref.mean()) / ref.std()
    with torch.no_grad():
        out = apply_model(model, x[None], device=device, split=True, overlap=0.25, progress=False)[0]
    voc = out[model.sources.index("vocals")] * ref.std() + ref.mean()
    write(dst, voc.cpu().numpy(), model.samplerate)
    return dst


def beats(src: Path, device: str = "cuda") -> tuple[list[float], list[float]]:
    """Times of beats and downbeats (s) from the whole recording (the drums are in the beat, not in the vocals)."""
    from beat_this.inference import Audio2Beats

    sr = 22050
    b, d = Audio2Beats(checkpoint_path="final0", device=device, dbn=False)(read(src, sr)[0], sr)
    return [float(t) for t in b], [float(t) for t in d]
