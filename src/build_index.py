import json
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
from src.config import FACTS_CSV_PATH, FAISS_INDEX_PATH, FACTS_META_PATH, EMBEDDING_MODEL_NAME

def load_facts():
    if not FACTS_CSV_PATH.exists():
        raise FileNotFoundError(f"facts.csv not found at {FACTS_CSV_PATH}")
    df = pd.read_csv(FACTS_CSV_PATH)
    required_cols = {"id", "source", "date", "statement"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"facts.csv must have columns: {required_cols}")
    return df

def build_embeddings(df):
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    sentences = df["statement"].tolist()
    embeddings = model.encode(sentences, show_progress_bar=True)
    return embeddings

def build_faiss_index(embeddings):
    import numpy as np
    embeddings = embeddings.astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def save_index(index):
    faiss.write_index(index, str(FAISS_INDEX_PATH))

def save_metadata(df):
    metadata = []
    for _, row in df.iterrows():
        metadata.append(
            {
                "id": str(row["id"]),
                "source": str(row["source"]),
                "date": str(row["date"]),
                "statement": str(row["statement"]),
            }
        )
    with open(FACTS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

def main():
    print("Loading facts...")
    df = load_facts()

    print("Building embeddings...")
    embeddings = build_embeddings(df)

    print("Building FAISS index...")
    index = build_faiss_index(embeddings)

    print(f"Saving FAISS index to {FAISS_INDEX_PATH}...")
    save_index(index)

    print(f"Saving metadata to {FACTS_META_PATH}...")
    save_metadata(df)

    print("Done.")

if __name__ == "__main__":
    main()
