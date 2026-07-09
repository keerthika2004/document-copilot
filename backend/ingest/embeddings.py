"""Local embedding generator using HuggingFace transformers (no API keys needed)."""

from __future__ import annotations

import torch
from transformers import AutoModel, AutoTokenizer

from app.config import settings


class EmbeddingService:
    """Generates text embeddings locally using a HuggingFace model."""

    def __init__(
        self,
        model_name: str | None = None,
        expected_dimensions: int | None = None,
    ) -> None:
        self.model_name = model_name or settings.embedding_model
        self.expected_dimensions = expected_dimensions or settings.embedding_dimensions

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.eval()

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts using local model inference."""
        if not texts:
            return []

        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )

        with torch.no_grad():
            outputs = self.model(**encoded)
            # Use CLS token embedding (first token) as sentence representation
            cls_embeddings = outputs.last_hidden_state[:, 0]
            # L2 normalize for cosine similarity
            embeddings = torch.nn.functional.normalize(cls_embeddings, p=2, dim=1)

        result = embeddings.tolist()

        # Verify dimensions
        if result and len(result[0]) != self.expected_dimensions:
            raise ValueError(
                f"Expected {self.expected_dimensions} dimensions, got {len(result[0])}"
            )

        return result
