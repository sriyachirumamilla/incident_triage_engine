# service handles the AI Part
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        # Uses setting variable or fallback model
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)

    def generate_vector(self, text: str) -> List[float]:
        """Converts a string of text into a 384-dimensional embedding."""
        if not text or not text.strip():
            return [0.0] * 384
            
        # Clean text to ensure better embedding quality
        cleaned_text = text.replace("\n", " ").strip()
        embedding = self.model.encode(cleaned_text)
        return embedding.tolist()

    # Alias so both method names work seamlessly
    def generate_embedding(self, text: str) -> List[float]:
        return self.generate_vector(text)


# Singleton instances (exposing both singular and plural so imports never fail)
embedding_service = EmbeddingService()
embedding_services = embedding_service