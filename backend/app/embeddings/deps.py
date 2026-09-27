"""FastAPI dependency for embedding providers."""

from functools import lru_cache

from app.config import Settings, get_settings
from app.embeddings.base import EmbeddingProvider
from app.embeddings.deterministic import DeterministicEmbeddingProvider


@lru_cache
def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    resolved = settings or get_settings()
    provider_name = resolved.embedding_provider.lower()
    if provider_name == "deterministic":
        return DeterministicEmbeddingProvider(dimensions=resolved.embedding_dimensions)
    raise ValueError(f"Unsupported embedding provider: {resolved.embedding_provider}")
