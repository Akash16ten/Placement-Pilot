"""Embedding backends.

* SentenceTransformerEmbedder — HuggingFace sentence-transformers (production path)
* HashingEmbedder            — dependency-free fallback (offline / CI / no model download)

Both return L2-normalised float32 matrices, so inner product == cosine similarity.
"""
from __future__ import annotations

import logging
import re
import zlib
from functools import lru_cache

import numpy as np

from ..config import settings

log = logging.getLogger("placementpilot.embeddings")


class HashingEmbedder:
    name = "hashing-fallback"
    dim = 512

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            toks = re.findall(r"[a-z0-9+#.]+", t.lower())
            feats = toks + [a + "_" + b for a, b in zip(toks, toks[1:])]
            for f in feats:
                h = zlib.crc32(f.encode())
                out[i, h % self.dim] += 1.0
            out[i] = np.log1p(out[i])
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (out / norms).astype(np.float32)


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # lazy import

        self.model = SentenceTransformer(model_name)
        self.name = model_name
        self.dim = self.model.get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        v = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(v, dtype=np.float32)


@lru_cache(maxsize=1)
def get_embedder():
    backend = settings.EMBEDDING_BACKEND
    if backend in ("auto", "st"):
        try:
            emb = SentenceTransformerEmbedder(settings.EMBEDDING_MODEL)
            log.info("Using HuggingFace embeddings: %s", emb.name)
            return emb
        except Exception as e:
            if backend == "st":
                raise
            log.warning("sentence-transformers unavailable (%s). Using hashing fallback.", e)
    return HashingEmbedder()


def is_semantic(embedder) -> bool:
    return not isinstance(embedder, HashingEmbedder)
