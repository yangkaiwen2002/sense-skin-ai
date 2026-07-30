"""
Embedding backend + FAISS index for the semantic-recall leg of the hybrid
retriever.

sentence-transformers / torch / faiss are heavy, optional dependencies —
importing them or downloading model weights can fail for many reasons (no
network, no disk space, incompatible build, first-run cold cache, ...).
Every failure mode here must be catchable by the caller (HybridRetriever in
retriever.py) so it can degrade to BM25 + TF-IDF only. This module never
decides to degrade itself — it just raises, and lets the caller decide.
"""
from __future__ import annotations

import logging
from typing import Protocol, Sequence

import numpy as np

logger = logging.getLogger(__name__)

# sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2:
# ~470MB, 384-dim, trained on 50+ languages including Chinese/English —
# a good size/quality tradeoff for a small local knowledge base like this one.
DEFAULT_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


class Embedder(Protocol):
    """Minimal interface HybridRetriever depends on.

    Production code uses SentenceTransformerEmbedder; tests inject a
    lightweight fake that implements the same `encode` signature without
    requiring torch or a network download.
    """

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        ...


class SentenceTransformerEmbedder:
    """Lazy-loading wrapper around sentence-transformers.

    The model is only imported/downloaded on the first `encode()` call, so
    constructing a retriever with FAISS disabled (enable_faiss=False) never
    touches torch at all.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        self.model_name = model_name
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import SentenceTransformer  # deferred heavy import
        self._model = SentenceTransformer(self.model_name)

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        self._load()
        vectors = self._model.encode(
            list(texts),
            normalize_embeddings=True,   # unit-norm vectors -> inner product == cosine similarity
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype="float32")


class FaissVectorIndex:
    """Thin wrapper around a FAISS IndexFlatIP over L2-normalized vectors
    (inner product on unit vectors == cosine similarity)."""

    def __init__(self, dim: int):
        import faiss  # deferred import — keeps faiss-cpu optional at module load time
        self._index = faiss.IndexFlatIP(dim)
        self._row_to_id: list[int] = []

    def build(self, ids: Sequence[int], vectors: np.ndarray) -> None:
        """Build the index once, at retriever-init time — never per query."""
        if vectors.ndim != 2 or vectors.shape[0] != len(ids):
            raise ValueError(f"ids/vectors length mismatch: {len(ids)} ids vs shape {vectors.shape}")
        self._index.add(vectors)
        self._row_to_id = list(ids)

    @property
    def ntotal(self) -> int:
        return self._index.ntotal

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[int, float]]:
        """Return up to top_k (entry_id, cosine_score) pairs, best first."""
        if self._index.ntotal == 0 or top_k <= 0:
            return []
        k = min(top_k, self._index.ntotal)
        scores, rows = self._index.search(query_vector, k)
        out: list[tuple[int, float]] = []
        for row, score in zip(rows[0], scores[0]):
            if row == -1:
                continue
            out.append((self._row_to_id[row], float(score)))
        return out


def build_faiss_index(
    ids: Sequence[int],
    corpus: Sequence[str],
    embedder: Embedder,
) -> FaissVectorIndex:
    """
    Encode `corpus` exactly once and build a FAISS IndexFlatIP index over it.
    Raises on any failure (model load, network, shape mismatch, faiss import) —
    the caller is responsible for catching and degrading gracefully.
    """
    vectors = embedder.encode(corpus)
    if vectors.ndim != 2 or vectors.shape[0] != len(corpus):
        raise ValueError(f"unexpected embedding shape {vectors.shape} for {len(corpus)} docs")
    index = FaissVectorIndex(dim=vectors.shape[1])
    index.build(ids, vectors)
    return index
