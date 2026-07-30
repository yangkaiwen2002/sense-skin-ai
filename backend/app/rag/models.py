"""
Typed data structures shared across the hybrid retrieval pipeline
(FAISS + BM25 + TF-IDF -> Reciprocal Rank Fusion).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeEntry:
    """One row of backend/data/knowledge.json."""
    id: int
    title: str
    category: str
    content: str


@dataclass
class RetrievalDetail:
    """Per-result breakdown of how each individual retriever scored/ranked a document.

    Fields are left as None when a given retriever was not active, or was
    active but did not return this document among its candidates.
    """
    faiss_rank:  Optional[int]   = None
    faiss_score: Optional[float] = None
    bm25_rank:   Optional[int]   = None
    bm25_score:  Optional[float] = None
    tfidf_rank:  Optional[int]   = None
    tfidf_score: Optional[float] = None
    active_retrievers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "faiss_rank":  self.faiss_rank,
            "faiss_score": self.faiss_score,
            "bm25_rank":   self.bm25_rank,
            "bm25_score":  self.bm25_score,
            "tfidf_rank":  self.tfidf_rank,
            "tfidf_score": self.tfidf_score,
            "active_retrievers": list(self.active_retrievers),
        }


@dataclass
class RetrievalResult:
    """One fused hybrid-search hit.

    `score` is kept as a backward-compat alias of `fused_score` because
    app/routers/rag.py and the frontend historically read a plain `score`
    field from the old single-engine TF-IDF retriever.
    """
    id: int
    title: str
    category: str
    content: str
    fused_score: float
    retrieval_details: RetrievalDetail

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "score": self.fused_score,        # backward-compat alias
            "fused_score": self.fused_score,
            "retrieval_details": self.retrieval_details.to_dict(),
        }


class KnowledgeBaseError(RuntimeError):
    """Raised when backend/data/knowledge.json is missing or malformed."""
