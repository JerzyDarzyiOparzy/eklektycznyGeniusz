"""Topics (plan, phase 5): clustering meaning vectors, not a fixed list.

- unit: a verse fragment = up to 4 consecutive lines of the rapper (chorus once), so topics catch a thought, not a line;
- vectors: sdadas/mmlw-roberta-large (Polish embeddings, MTEB-PL), GPU in fp16;
- clustering: BERTopic (UMAP + HDBSCAN in „leaf” mode) with a fixed seed; topic keywords computed on the lemmas of
  content words;
- clusters are named by a person (config/topics.yaml); until then, working names from the most frequent words;
- parameters and counts are saved with the results in data/topics/topics.json.
"""
import json

import numpy as np
import pandas as pd

from rapdna import paths
from rapdna.text.nlp import FUNCTION_WORDS

OUT = paths.DATA / "topics"
MODEL = "sdadas/mmlw-roberta-large"
CHUNK = 4
SEED = 2026
MIN_TOPIC = 30
NAMES = paths.CONFIG / "topics.yaml"


def chunks() -> pd.DataFrame:
    lines = pd.read_parquet(paths.PARQUET / "lines.parquet")
    words = pd.read_parquet(paths.PARQUET / "words.parquet")
    lines = lines[lines.attributed & ~lines.is_dup].sort_values(["song_id", "section", "line"])
    content = words[~words.function & (words.form.str.len() >= 3)]
    lem = content.groupby("line_uid").lemma.apply(lambda s: " ".join(s.str.lower()))
    rows = []
    for (sid, sec), g in lines.groupby(["song_id", "section"], sort=False):
        g = g.reset_index(drop=True)
        for start in range(0, len(g), CHUNK):
            part = g.iloc[start:start + CHUNK]
            rows.append({"artist": part.artist.iloc[0], "album": part.album.iloc[0], "song_id": sid,
                         "title": part.title.iloc[0], "text": "\n".join(part.text),
                         "lemmas": " ".join(lem.get(u, "") for u in part.line_uid)})
    return pd.DataFrame(rows)


def embed(texts: list[str], log=print) -> np.ndarray:
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / "embeddings.npy"
    if cache.exists():
        e = np.load(cache)
        if len(e) == len(texts):
            return e
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    log(f"{MODEL} embeddings on {device}: {len(texts)} fragments…")
    model = SentenceTransformer(MODEL, device=device)
    if device == "cuda":
        model.half()
    e = model.encode(texts, batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    np.save(cache, e)
    return e


def fit(log=print) -> dict:
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    df = chunks()
    emb = embed(list(df.text), log=log)
    stop = sorted(FUNCTION_WORDS | {"być", "mieć", "móc", "chcieć", "wiedzieć", "taki", "tylko", "jeszcze", "już",
                                    "kurwa", "jebać", "chuj", "ziom", "ziomek", "yeah", "ej", "się", "nie", "mówić", "robić",
                                    "dać", "iść", "widzieć", "czuć", "brać", "lubić", "musieć", "tutaj", "zawsze",
                                    "wtedy", "sam", "cały", "każdy", "ciągle", "znowu", "nigdy", "dziś"})
    model = BERTopic(
        umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=SEED),
        # „leaf”: smaller, more coherent clusters; the default mode merged rap lyrics into 2 huge clusters
        hdbscan_model=HDBSCAN(min_cluster_size=MIN_TOPIC, min_samples=5, metric="euclidean",
                              cluster_selection_method="leaf", prediction_data=True),
        vectorizer_model=CountVectorizer(stop_words=stop, min_df=1, token_pattern=r"(?u)\b[^\W\d_]{3,}\b"),
        language="multilingual",  # the English mode strips Polish letters from the keywords
        calculate_probabilities=False, verbose=False,
    )
    topics, _ = model.fit_transform(list(df.lemmas), embeddings=emb)
    df["topic"] = topics
    info = model.get_topic_info()
    words = {int(t): [w for w, _ in model.get_topic(t)[:10]] for t in info.Topic if t != -1}
    examples = {int(t): df[df.topic == t].sample(min(3, (df.topic == t).sum()), random_state=SEED).text.tolist()
                for t in words}
    names = _load_names()
    topic_list = [{"id": t, "name": names.get(t) or ", ".join(w[:3]), "working_name": t not in names,
                   "words": w, "count": int((df.topic == t).sum()), "examples": examples[t]} for t, w in words.items()]
    known = df[df.topic != -1]
    per_artist = pd.crosstab(known.artist, known.topic, normalize="index")
    per_artist.columns = [int(c) for c in per_artist.columns]
    OUT.mkdir(parents=True, exist_ok=True)
    df[["artist", "album", "song_id", "title", "topic"]].to_parquet(OUT / "chunks.parquet", index=False)
    meta = {"model": MODEL, "chunk_lines": CHUNK, "seed": SEED, "min_topic": MIN_TOPIC, "fragments": len(df),
            "topics": len(words), "noise": int((df.topic == -1).sum())}
    result = {"meta": meta, "topics": topic_list,
              "per_artist": {a: {int(k): round(float(v), 4) for k, v in r.items()} for a, r in per_artist.iterrows()}}
    (OUT / "topics.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def _load_names() -> dict[int, str]:
    if not NAMES.exists():
        return {}
    import yaml

    return {int(k): v for k, v in (yaml.safe_load(NAMES.read_text(encoding="utf-8")) or {}).items() if v}
