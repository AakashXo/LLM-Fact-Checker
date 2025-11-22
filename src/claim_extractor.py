import spacy
from typing import List, Dict
from src.config import SPACY_MODEL_NAME

class ClaimExtractor:
    def __init__(self):
        self.nlp = spacy.load(SPACY_MODEL_NAME)

    def extract_claims(self, text: str) -> List[Dict]:
        """
        Returns a list of dicts: { 'sentence': str, 'entities': [str] }
        """
        doc = self.nlp(text)
        claims = []

        for sent in doc.sents:
            sent_doc = self.nlp(sent.text)
            entities = [ent.text for ent in sent_doc.ents]
            has_verb = any(token.pos_ == "VERB" for token in sent_doc)

            if entities and has_verb:
                claims.append(
                    {
                        "sentence": sent.text.strip(),
                        "entities": entities,
                    }
                )
        # Fallback: if nothing matched, treat full text as one claim
        return claims

if __name__ == "__main__":
    extractor = ClaimExtractor()
    sample = "The Indian government has announced free electricity to all farmers starting July 2025."
    print(extractor.extract_claims(sample))
