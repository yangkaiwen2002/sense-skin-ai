"""
Lightweight TF-IDF retriever for the SkinSense knowledge base.
No external embedding API needed — runs fully locally using scikit-learn.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import TypedDict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge.json"


class KnowledgeEntry(TypedDict):
    id: int
    title: str
    category: str
    content: str


class Retriever:
    """In-memory TF-IDF retriever over the knowledge base."""

    def __init__(self, data_path: str | Path = _DATA_PATH):
        self._entries: list[KnowledgeEntry] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._matrix = None
        self._load(data_path)

    def _load(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            self._entries = json.load(f)

        if not self._entries:
            return

        # Build corpus: combine title + content for richer matching
        corpus = [
            f"{e['title']} {e.get('category', '')} {e['content']}"
            for e in self._entries
        ]

        # char_wb n-grams work well for mixed Chinese/English text
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
            sublinear_tf=True,
        )
        self._matrix = self._vectorizer.fit_transform(corpus)

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """Return top-k most relevant knowledge entries for the question."""
        if not self._entries or self._vectorizer is None:
            return []

        q_vec = self._vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] < 0.01:   # Skip near-zero matches
                continue
            entry = self._entries[idx]
            results.append({
                "id": entry["id"],
                "title": entry["title"],
                "category": entry.get("category", ""),
                "content": entry["content"],
                "score": float(scores[idx]),
            })
        return results

    def format_context(self, entries: list[dict]) -> str:
        """Format retrieved entries into a context block for the prompt."""
        if not entries:
            return "（未找到相关知识库内容）"
        parts = []
        for i, e in enumerate(entries, 1):
            parts.append(f"[知识 {i}] {e['title']}\n{e['content']}")
        return "\n\n".join(parts)


# Singleton — loaded once at import time
_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
