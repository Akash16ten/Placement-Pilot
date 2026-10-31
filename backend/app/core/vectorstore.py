"""FAISS-backed vector store (numpy brute-force fallback if faiss is unavailable)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

try:
    import faiss  # type: ignore

    HAS_FAISS = True
except Exception:  # pragma: no cover
    faiss = None
    HAS_FAISS = False


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        self.metas: list[dict] = []
        self._vecs = np.zeros((0, dim), dtype=np.float32)  # kept for fallback + persistence
        self.index = faiss.IndexFlatIP(dim) if HAS_FAISS else None

    def __len__(self) -> int:
        return len(self.metas)

    def add(self, vectors: np.ndarray, metas: list[dict]) -> None:
        if len(vectors) == 0:
            return
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        assert vectors.shape[1] == self.dim and len(vectors) == len(metas)
        if self.index is not None:
            self.index.add(vectors)
        self._vecs = np.vstack([self._vecs, vectors])
        self.metas.extend(metas)

    def search(self, query_vec: np.ndarray, k: int = 5) -> list[tuple[float, dict]]:
        if not len(self.metas):
            return []
        q = np.ascontiguousarray(query_vec.reshape(1, -1), dtype=np.float32)
        k = min(k, len(self.metas))
        if self.index is not None:
            scores, ids = self.index.search(q, k)
            return [(float(s), self.metas[i]) for s, i in zip(scores[0], ids[0]) if i >= 0]
        sims = (self._vecs @ q.T).ravel()
        top = np.argsort(-sims)[:k]
        return [(float(sims[i]), self.metas[i]) for i in top]

    def max_similarity(self, queries: np.ndarray) -> np.ndarray:
        """For each query vector, the best cosine similarity against the store."""
        if not len(self.metas):
            return np.zeros(len(queries))
        return (np.asarray(queries, dtype=np.float32) @ self._vecs.T).max(axis=1)

    # ---- persistence -------------------------------------------------
    def save(self, directory: Path, name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, str(directory / f"{name}.faiss"))
        np.save(directory / f"{name}.npy", self._vecs)
        (directory / f"{name}.json").write_text(json.dumps(self.metas), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path, name: str) -> "VectorStore":
        vecs = np.load(directory / f"{name}.npy")
        metas = json.loads((directory / f"{name}.json").read_text(encoding="utf-8"))
        store = cls(vecs.shape[1])
        store.add(vecs, metas)
        return store
