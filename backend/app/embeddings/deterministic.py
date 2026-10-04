"""Deterministic bag-of-words embeddings for tests and local MVP demos."""

from __future__ import annotations

import math
import re


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class DeterministicEmbeddingProvider:
    """Hash tokens into a fixed-size vector and L2-normalize."""

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions < 8:
            raise ValueError("Embedding dimensions must be at least 8.")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    async def embed(self, text: str) -> list[float]:
        return self._embed_sync(text)

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_sync(text) for text in texts]

    def _embed_sync(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions
        for token in _tokenize(text):
            index = hash(token) % self._dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector
        return [value / norm for value in vector]
