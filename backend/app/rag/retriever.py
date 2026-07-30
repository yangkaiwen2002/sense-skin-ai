"""
Hybrid retriever for the SkinSense knowledge base: FAISS (semantic) +
BM25 (keyword) + character-level TF-IDF (exact CN/EN substrings), combined
with weighted Reciprocal Rank Fusion (RRF).

Backward compatibility contract (app/routers/rag.py depends on this):
  - `get_retriever()` returns a process-wide singleton.
  - `.query(question, top_k=3) -> list[dict]`, each dict has at least
    `id`, `title`, `category`, `content`, `score`.
  - `.format_context(entries) -> str`.
`score` is now an alias for the fused RRF score; the richer breakdown is
additionally available under `fused_score` / `retrieval_details`.

FAISS is a soft dependency: if the embedding model can't be loaded (no
network, no local cache, faiss-cpu missing, etc.) the retriever logs a
warning and continues serving BM25 + TF-IDF only — it never raises out of
`query()` because of that.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.rag.embeddings import Embedder, SentenceTransformerEmbedder, build_faiss_index
from app.rag.fusion import DEFAULT_RRF_K, FusionWeights, reciprocal_rank_fusion
from app.rag.models import KnowledgeBaseError, KnowledgeEntry, RetrievalDetail, RetrievalResult
from app.rag.tokenization import tokenize

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge.json"
MAX_TOP_K = 20   # hard upper bound so a bad top_k value can't blow up candidate_k / result size


def _doc_text(entry: KnowledgeEntry) -> str:
    """Corpus text shared by all three retrievers (title carries a lot of signal)."""
    return f"{entry.title} {entry.category} {entry.content}"


class _TfidfEngine:
    """Character-level TF-IDF (char_wb, 2-4 grams) — good at exact CN/EN
    substrings, abbreviations and item names, weak at paraphrase/semantics."""

    def __init__(self, ids: list[int], corpus: list[str]):
        self._ids = ids
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._matrix = None
        if not corpus:
            return
        try:
            self._vectorizer = TfidfVectorizer(
                analyzer="char_wb", ngram_range=(2, 4), min_df=1, sublinear_tf=True,
            )
            self._matrix = self._vectorizer.fit_transform(corpus)
        except ValueError as exc:  # e.g. empty vocabulary
            logger.warning("TF-IDF index unavailable: %s", exc)
            self._vectorizer = None
            self._matrix = None

    @property
    def ready(self) -> bool:
        return self._vectorizer is not None

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        if not self.ready or top_k <= 0:
            return []
        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        order = np.argsort(scores)[::-1]
        out: list[tuple[int, float]] = []
        for idx in order:
            if scores[idx] < 0.01:   # scores are sorted desc -> nothing further clears the bar
                break
            out.append((self._ids[idx], float(scores[idx])))
            if len(out) >= top_k:
                break
        return out


class _Bm25Engine:
    """BM25Okapi over the mixed CN/EN tokenizer — strong on keyword / term overlap."""

    def __init__(self, ids: list[int], corpus: list[str]):
        self._ids = ids
        self._bm25: Optional[BM25Okapi] = None
        if not corpus:
            return
        try:
            tokenized = [tokenize(doc) or ["<empty>"] for doc in corpus]
            self._bm25 = BM25Okapi(tokenized)
        except (ValueError, ZeroDivisionError) as exc:
            logger.warning("BM25 index unavailable: %s", exc)
            self._bm25 = None

    @property
    def ready(self) -> bool:
        return self._bm25 is not None

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        if not self.ready or top_k <= 0:
            return []
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        order = np.argsort(scores)[::-1]
        out: list[tuple[int, float]] = []
        for idx in order:
            if scores[idx] <= 0:
                break
            out.append((self._ids[idx], float(scores[idx])))
            if len(out) >= top_k:
                break
        return out


class _FaissEngine:
    """Semantic recall via sentence-transformers + FAISS IndexFlatIP.

    Never raises: any failure during index construction is caught and
    turned into `ready == False` + `disabled_reason`, so the retriever can
    degrade to BM25 + TF-IDF.
    """

    def __init__(self, ids: list[int], corpus: list[str], embedder: Embedder, enabled: bool):
        self._index = None
        self._embedder = embedder
        self.disabled_reason: Optional[str] = None

        if not enabled:
            self.disabled_reason = "faiss disabled by configuration"
            return
        if not corpus:
            self.disabled_reason = "empty knowledge base"
            return

        try:
            self._index = build_faiss_index(ids, corpus, embedder)
        except Exception as exc:  # noqa: BLE001 - network/model/import/faiss failures all land here
            logger.warning(
                "FAISS semantic index unavailable, degrading to BM25+TF-IDF only: %s", exc
            )
            self.disabled_reason = str(exc)
            self._index = None

    @property
    def ready(self) -> bool:
        return self._index is not None

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        if not self.ready or top_k <= 0:
            return []
        try:
            q_vec = self._embedder.encode([query])
            return self._index.search(q_vec, top_k)
        except Exception as exc:  # noqa: BLE001 - a query-time failure must not crash the API
            logger.warning("FAISS query failed, returning no semantic hits: %s", exc)
            return []


class HybridRetriever:
    """FAISS + BM25 + TF-IDF retriever over the SkinSense knowledge base, fused with RRF."""

    def __init__(
        self,
        data_path: str | Path = _DATA_PATH,
        embedder: Optional[Embedder] = None,
        enable_faiss: bool = True,
        weights: Optional[dict[str, float]] = None,
        rrf_k: int = DEFAULT_RRF_K,
    ):
        self._weights = dict(weights) if weights else FusionWeights.as_dict()
        self._rrf_k = rrf_k

        self._entries_ordered: list[KnowledgeEntry] = []
        self._entries_by_id: dict[int, KnowledgeEntry] = {}
        self._load(data_path)

        ids    = [e.id for e in self._entries_ordered]
        corpus = [_doc_text(e) for e in self._entries_ordered]

        self._tfidf = _TfidfEngine(ids, corpus)
        self._bm25  = _Bm25Engine(ids, corpus)
        self._faiss = _FaissEngine(ids, corpus, embedder or SentenceTransformerEmbedder(), enable_faiss)

    # ── loading ────────────────────────────────────────────────────────────
    def _load(self, path: str | Path) -> None:
        path = Path(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError as exc:
            raise KnowledgeBaseError(f"知识库文件不存在: {path}") from exc
        except json.JSONDecodeError as exc:
            raise KnowledgeBaseError(f"知识库文件 JSON 格式错误: {path} ({exc})") from exc

        if not isinstance(raw, list):
            raise KnowledgeBaseError(f"知识库文件格式错误，期望 JSON 数组: {path}")

        entries: list[KnowledgeEntry] = []
        for item in raw:
            try:
                entries.append(KnowledgeEntry(
                    id=item["id"],
                    title=item["title"],
                    category=item.get("category", ""),
                    content=item["content"],
                ))
            except (KeyError, TypeError) as exc:
                raise KnowledgeBaseError(f"知识库条目缺少必要字段 (id/title/content): {item!r}") from exc

        self._entries_ordered = entries
        self._entries_by_id = {e.id: e for e in entries}

    # ── introspection ─────────────────────────────────────────────────────
    @property
    def active_retrievers(self) -> list[str]:
        """Which of the three engines actually initialised successfully."""
        active = []
        if self._tfidf.ready:
            active.append("tfidf")
        if self._bm25.ready:
            active.append("bm25")
        if self._faiss.ready:
            active.append("faiss")
        return active

    @property
    def faiss_disabled_reason(self) -> Optional[str]:
        return self._faiss.disabled_reason

    # ── query ─────────────────────────────────────────────────────────────
    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """Return up to `top_k` fused hits for `question`.

        Empty questions or an empty knowledge base return `[]` rather than
        raising — callers that need a hard validation error (e.g. the HTTP
        API) should check the input themselves before calling this.
        """
        if not question or not question.strip():
            return []
        if not self._entries_ordered:
            return []

        top_k = max(1, min(top_k, MAX_TOP_K))
        candidate_k = max(top_k * 4, 10)

        ranked_lists: dict[str, list[tuple[int, float]]] = {}
        if self._tfidf.ready:
            ranked_lists["tfidf"] = self._tfidf.search(question, candidate_k)
        if self._bm25.ready:
            ranked_lists["bm25"] = self._bm25.search(question, candidate_k)
        if self._faiss.ready:
            ranked_lists["faiss"] = self._faiss.search(question, candidate_k)

        if not ranked_lists:
            return []

        fused_hits = reciprocal_rank_fusion(ranked_lists, self._weights, k=self._rrf_k)
        active = self.active_retrievers

        results: list[dict] = []
        for hit in fused_hits[:top_k]:
            entry = self._entries_by_id.get(hit.doc_id)
            if entry is None:
                continue
            detail = RetrievalDetail(active_retrievers=active)
            for name, info in hit.per_retriever.items():
                setattr(detail, f"{name}_rank", info["rank"])
                setattr(detail, f"{name}_score", info["score"])
            result = RetrievalResult(
                id=entry.id,
                title=entry.title,
                category=entry.category,
                content=entry.content,
                fused_score=round(hit.fused_score, 6),
                retrieval_details=detail,
            )
            results.append(result.to_dict())
        return results

    def format_context(self, entries: list[dict]) -> str:
        """Format retrieved entries into a context block for the prompt. Unchanged
        from the original TF-IDF-only retriever's contract."""
        if not entries:
            return "（未找到相关知识库内容）"
        parts = []
        for i, e in enumerate(entries, 1):
            parts.append(f"[知识 {i}] {e['title']}\n{e['content']}")
        return "\n\n".join(parts)


# Backward-compat alias: earlier code referred to this class as `Retriever`.
Retriever = HybridRetriever


# Singleton — built once per process on first use, exactly like the old retriever.
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        from app.config import settings
        _retriever = HybridRetriever(
            embedder=SentenceTransformerEmbedder(settings.RAG_EMBEDDING_MODEL),
            enable_faiss=settings.RAG_ENABLE_FAISS,
        )
    return _retriever
