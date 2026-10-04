"""Embedding provider abstraction for document RAG."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    @property
    def dimensions(self) -> int:
        """Vector dimension produced by this provider."""

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts."""
