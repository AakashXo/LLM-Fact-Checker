from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FACTS_CSV_PATH = DATA_DIR / "facts.csv"
FAISS_INDEX_PATH = DATA_DIR / "faiss_index.bin"
FACTS_META_PATH = DATA_DIR / "facts_metadata.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SPACY_MODEL_NAME = "en_core_web_sm"

TOP_K = 5

OPENAI_MODEL_NAME = "gpt-4o-mini"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
