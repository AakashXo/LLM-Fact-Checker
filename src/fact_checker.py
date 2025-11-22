import json
import re
from typing import List, Dict, Any

import faiss
from sentence_transformers import SentenceTransformer

from src.config import (
    FACTS_META_PATH,
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    TOP_K,
)
from src.claim_extractor import ClaimExtractor


def extract_numbers(text: str):
    """
    Extract numeric values from text as floats.
    Example: "₹39.84 crore" -> [39.84]
    """
    nums = re.findall(r"\d+(?:\.\d+)?", text.replace(",", ""))
    return [float(n) for n in nums]


class VectorStore:
    def __init__(self):
        if not FAISS_INDEX_PATH.exists():
            raise FileNotFoundError("FAISS index not found, run build_index.py first.")
        if not FACTS_META_PATH.exists():
            raise FileNotFoundError("facts_metadata.json not found, run build_index.py first.")

        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        with open(FACTS_META_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.embedder = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
        q_emb = self.embedder.encode([query]).astype("float32")
        distances, indices = self.index.search(q_emb, top_k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            meta = dict(self.metadata[idx])  # copy so we don't mutate original
            meta["score"] = float(dist)
            results.append(meta)
        return results


class FactChecker:
    """
    Fact Checker:
    1. Extract claims using ClaimExtractor (spaCy).
    2. Retrieve closest PIB facts using FAISS.
    3. Compare numbers between claim and official facts:
       - If close (<=20% diff) -> True
       - If conflicting -> False
       - Otherwise -> Unverifiable
    """

    def __init__(self):
        self.vector_store = VectorStore()
        self.claim_extractor = ClaimExtractor()

    def classify_claim(self, claim: str) -> Dict[str, Any]:
        retrieved = self.vector_store.retrieve(claim)

        if not retrieved:
            return {
                "claim": claim,
                "retrieved_facts": [],
                "verdict": "Unverifiable",
                "reasoning": "No relevant official facts were retrieved for this claim.",
                "evidence": [],
            }

        # Use top retrieved fact
        top_fact = retrieved[0]["statement"]

        # Extract numbers
        claim_nums = extract_numbers(claim)
        fact_nums = extract_numbers(top_fact)

        # Default: no evidence for Unverifiable
        evidence: List[str] = []

        # Numeric comparison
        if claim_nums and fact_nums:
            c = claim_nums[0]
            f = fact_nums[0]
            rel_diff = abs(c - f) / max(abs(f), 1e-6)

            if rel_diff <= 0.2:
                verdict = "True"
                reasoning = (
                    f"The claim mentions {c}, which is close to the official PIB figure {f}. "
                    f"This matches the retrieved evidence."
                )
                evidence = [fact["statement"] for fact in retrieved[:3]]

            else:
                verdict = "False"
                reasoning = (
                    f"The claim mentions {c}, but the official PIB figure is {f}, which is significantly different. "
                    f"Therefore, the claim is considered False."
                )
                evidence = [fact["statement"] for fact in retrieved[:3]]

        else:
            verdict = "Unverifiable"
            reasoning = (
                "The claim does not contain numeric information comparable to official PIB facts, "
                "or the retrieved fact does not match closely enough to verify."
            )
            evidence = []  # No evidence for Unverifiable

        return {
            "claim": claim,
            "retrieved_facts": retrieved,
            "verdict": verdict,
            "reasoning": reasoning,
            "evidence": evidence,
        }

    def fact_check_text(self, text: str) -> List[Dict[str, Any]]:
        claims = self.claim_extractor.extract_claims(text)
        if not claims:
            return []
        return [self.classify_claim(c["sentence"]) for c in claims]


if __name__ == "__main__":
    checker = FactChecker()
    sample_text = "NBA released around ₹39.84 crore to Andhra Pradesh for Red Sanders protection and conservation."
    output = checker.fact_check_text(sample_text)
    print(json.dumps(output, indent=2, ensure_ascii=False))
