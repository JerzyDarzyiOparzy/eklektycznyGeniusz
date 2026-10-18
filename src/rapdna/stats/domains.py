"""Vocabulary domains (plan, phase 5: „metaphor domains: sport, war, food, religion, games”).

Methodological note: this counts the share of words from a domain, it does not detect metaphors (that needs judging
meaning in context). The lexicons are listed by hand in config/domains.yaml (lemmas). Expansion with
mmlw-roberta-large embeddings was tested and rejected: a sentence model places single words at random.
`lexicons()` writes the lexicons to data/topics/domain_lexicons.json (optional expansion with `expand=True`).
"""
import json

import numpy as np
import pandas as pd
import yaml

from rapdna import paths
from rapdna.stats.topics import MODEL, OUT

SEEDS = paths.CONFIG / "domains.yaml"
MIN_Z = 3.0  # a word must stand out from the background: similarity ≥ mean + 3 standard deviations
MAX_EXPANSION = 80
MIN_FREQ = 3


def lexicons(log=print, expand: bool = False) -> dict[str, list[str]]:
    if not expand:
        lex = {k: sorted(set(v)) for k, v in yaml.safe_load(SEEDS.read_text(encoding="utf-8")).items()}
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "domain_lexicons.json").write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")
        return lex
    import torch
    from sentence_transformers import SentenceTransformer

    seeds = yaml.safe_load(SEEDS.read_text(encoding="utf-8"))
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    content = words[~words.function & words.pos.isin(["NOUN", "VERB", "ADJ"]) & (words.lemma.str.len() >= 3)]
    freq = content.lemma.str.lower().value_counts()
    vocab = sorted(freq[freq >= MIN_FREQ].index)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(MODEL, device=device)
    if device == "cuda":
        model.half()
    log(f"lemma embeddings: {len(vocab)}")
    V = model.encode(vocab, batch_size=256, normalize_embeddings=True, show_progress_bar=False)
    out = {}
    for name, seed_words in seeds.items():
        S = model.encode(seed_words, normalize_embeddings=True, show_progress_bar=False)
        centroid = S.mean(axis=0)
        centroid /= np.linalg.norm(centroid)
        sims = V @ centroid
        z = (sims - sims.mean()) / sims.std()
        expanded = [vocab[i] for i in np.argsort(-sims)[:MAX_EXPANSION] if z[i] >= MIN_Z]
        out[name] = sorted(set(seed_words) | set(expanded))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "domain_lexicons.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def domain_shares(words: pd.DataFrame, lex: dict[str, list[str]]) -> dict[str, float]:
    content = words[~words.function]
    lem = content.lemma.str.lower()
    return {f"domain_{k}_1000": 1000 * lem.isin(set(v)).sum() / max(len(words), 1) for k, v in lex.items()}
