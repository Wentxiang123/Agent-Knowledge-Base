"""Embedding provider integration."""

import hashlib
import math
import os
from typing import Any

import httpx
from fastapi import HTTPException, status

DEFAULT_LOCAL_EMBEDDING_DIMENSION = 384


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _openai_embeddings_endpoint(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return f"{base_url}/embeddings"
    return f"{base_url}/v1/embeddings"


def _local_embedding(text: str, dimension: int = DEFAULT_LOCAL_EMBEDDING_DIMENSION) -> list[float]:
    vector = [0.0] * dimension
    normalized = _normalize_text(text).lower()
    if not normalized:
        return vector

    features = list(normalized)
    features.extend(normalized[index : index + 2] for index in range(max(len(normalized) - 1, 0)))

    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


class EmbeddingService:
    def __init__(self) -> None:
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        self.base_url = os.getenv("EMBEDDING_BASE_URL")
        self.model = os.getenv("EMBEDDING_MODEL")
        self.timeout_seconds = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

    @property
    def use_remote_provider(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        normalized_texts = [_normalize_text(text) for text in texts]
        if any(not text for text in normalized_texts):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="embedding input text cannot be empty",
            )
        if self.use_remote_provider:
            return self._embed_with_remote_provider(normalized_texts)
        return [_local_embedding(text) for text in normalized_texts]

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _embed_with_remote_provider(self, texts: list[str]) -> list[list[float]]:
        endpoint = _openai_embeddings_endpoint(self.base_url or "")
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"model": self.model, "input": texts}

        try:
            response = httpx.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            body: dict[str, Any] = response.json()
            data = sorted(body.get("data", []), key=lambda item: item.get("index", 0))
            embeddings = [item.get("embedding") for item in data]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"embedding provider failed: {exc}",
            ) from exc

        if len(embeddings) != len(texts) or any(not isinstance(item, list) for item in embeddings):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="embedding provider returned an invalid response",
            )
        return embeddings


embedding_service = EmbeddingService()
