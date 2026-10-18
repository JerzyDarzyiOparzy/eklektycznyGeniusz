"""Audio layer (phase 4 of the plan, pilot): recording → vocals → words in time → beats. Plan and criteria:
docs/en/roadmap.md. Audio files stay local in data/audio/ (gitignored)."""
from rapdna import paths

AUDIO = paths.DATA / "audio"
RAW = AUDIO / "raw"          # <song_id>.wav, the whole recording
VOCALS = AUDIO / "vocals"    # <song_id>.wav, vocals from Demucs
ALIGN = AUDIO / "align"      # <song_id>.json, words in time and beats
VIEW = AUDIO / "view"        # <song_id>.html, karaoke page for listening checks (full lyrics, do not publish)
