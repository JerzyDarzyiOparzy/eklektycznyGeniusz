from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
RESOURCES = ROOT / "resources"
DATA = ROOT / "data"
RAW_HTML = DATA / "raw_html"
LYRICS = DATA / "lyrics"
PARQUET = DATA / "parquet"
STATS = DATA / "stats"
SITE = ROOT / "site"

PANPHON_SIMILARITY = RESOURCES / "panphon_similarity.csv"  # preview of the matrix computed from PanPhon features
PHONETIC_DICT = RESOURCES / "phonetic_dict.parquet"
PHONETIC_DICT_URL = ("https://github.com/JerzyDarzyiOparzy/eklektycznyGeniusz/releases/download/"
                     "phonetic-dictionary-v1/phonetic-dictionary.zip")
HOMONYMS = RESOURCES / "homonyms_cleaned.json"  # optional: plWordNet senses, for polysemy candidates
SLANG = RESOURCES / "slownik_miejski.csv"  # optional: headwords of miejski.pl (Polish urban dictionary), column `word`
