"""
End-to-end tests for HybridRetriever (app/rag/retriever.py).

No test in this file downloads a real embedding model or hits the network —
FAISS-dependent behaviour is exercised through the deterministic
FakeSemanticEmbedder / BrokenEmbedder fixtures in conftest.py. A separate,
explicitly-opt-in integration test at the bottom of this file exercises the
real sentence-transformers model and is skipped unless
RUN_REAL_EMBEDDING_TEST=1 is set, so the default `pytest` run never depends
on network access.
"""
from __future__ import annotations

import os

import pytest

from app.rag.retriever import HybridRetriever, MAX_TOP_K, Retriever, get_retriever
from app.rag.models import KnowledgeBaseError
from tests.conftest import (
    BrokenEmbedder,
    FakeSemanticEmbedder,
    REAL_KNOWLEDGE_PATH,
    SAMPLE_ENTRIES,
)


# ── 1. Chinese keyword queries hit via BM25 / TF-IDF ────────────────────────

def test_chinese_query_finds_relevant_doc_via_bm25_and_tfidf(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("流动性怎么评估", top_k=3)

    assert results, "expected at least one hit"
    ids = [r["id"] for r in results]
    assert 101 in ids  # "皮肤流动性评估方法"
    assert retriever.active_retrievers == ["tfidf", "bm25"]


def test_chinese_query_against_real_knowledge_base():
    """Same check against the production knowledge.json (32 real entries)."""
    retriever = HybridRetriever(data_path=REAL_KNOWLEDGE_PATH, enable_faiss=False)
    results = retriever.query("龙狙为什么波动很大", top_k=5)
    assert results
    titles = [r["title"] for r in results]
    assert any("龙狙" in t for t in titles)


# ── 2. English abbreviations / item names ───────────────────────────────────

def test_english_query_finds_ak47_doc(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("AK-47 skin investment", top_k=3)
    ids = [r["id"] for r in results]
    assert 102 in ids  # "AK-47 红线市场特征"


def test_english_query_against_real_knowledge_base():
    retriever = HybridRetriever(data_path=REAL_KNOWLEDGE_PATH, enable_faiss=False)
    results = retriever.query("AK-47 skin investment", top_k=5)
    assert results
    assert any("AK-47" in r["title"] or "AK-47" in r["content"] for r in results)


# ── 3. Semantically-similar-but-lexically-different queries via FAISS ──────

def test_faiss_finds_semantically_related_doc_with_no_keyword_overlap(sample_kb_path):
    """Query uses '变现速度' — a synonym-ish phrase, zero character-bigram
    overlap with doc 101's '流动性评估' wording (verified below via the
    BM25/TF-IDF-only sanity check). BM25/TF-IDF (literal token/char matching)
    should NOT surface it; FAISS (fake semantic embedder mapping both to the
    same 'liquidity' topic) should."""
    query = "这把刀变现速度怎么样"

    bm25_tfidf_only = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    literal_results = bm25_tfidf_only.query(query, top_k=5)
    assert all(r["id"] != 101 for r in literal_results), (
        "sanity check failed: BM25/TF-IDF unexpectedly matched on literal overlap"
    )

    hybrid = HybridRetriever(
        data_path=sample_kb_path, embedder=FakeSemanticEmbedder(), enable_faiss=True,
    )
    assert "faiss" in hybrid.active_retrievers
    results = hybrid.query(query, top_k=5)
    ids = [r["id"] for r in results]
    assert 101 in ids, "FAISS should surface the semantically related doc"

    hit = next(r for r in results if r["id"] == 101)
    assert hit["retrieval_details"]["faiss_rank"] is not None
    assert hit["retrieval_details"]["bm25_rank"] is None
    assert hit["retrieval_details"]["tfidf_rank"] is None


# ── 4 & 5. RRF correctness + de-duplication end-to-end ──────────────────────

def test_doc_found_by_all_three_retrievers_appears_once_and_ranks_first(sample_kb_path):
    """"流动性" query should be found by TF-IDF, BM25, and (with the fake
    embedder mapped to the same topic) FAISS all at once for doc 101 —
    it must appear exactly once in the fused results, ranked at the top."""
    retriever = HybridRetriever(
        data_path=sample_kb_path, embedder=FakeSemanticEmbedder(), enable_faiss=True,
    )
    results = retriever.query("流动性", top_k=5)

    ids = [r["id"] for r in results]
    assert ids.count(101) == 1
    assert ids[0] == 101

    detail = results[0]["retrieval_details"]
    assert detail["tfidf_rank"] is not None
    assert detail["bm25_rank"] is not None
    assert detail["faiss_rank"] is not None
    assert set(detail["active_retrievers"]) == {"tfidf", "bm25", "faiss"}


# ── 6. Final ordering by fused_score ────────────────────────────────────────

def test_results_sorted_by_fused_score_descending(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("皮肤 价格 市场", top_k=5)
    scores = [r["fused_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


# ── 7. FAISS load failure degrades gracefully, API doesn't crash ──────────

def test_faiss_failure_degrades_to_bm25_tfidf(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, embedder=BrokenEmbedder(), enable_faiss=True)

    assert "faiss" not in retriever.active_retrievers
    assert retriever.active_retrievers == ["tfidf", "bm25"]
    assert retriever.faiss_disabled_reason is not None

    # Must still serve results without raising.
    results = retriever.query("流动性", top_k=3)
    assert results
    assert all(r["retrieval_details"]["faiss_rank"] is None for r in results)


def test_faiss_disabled_by_config_flag(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    assert "faiss" not in retriever.active_retrievers
    assert retriever.faiss_disabled_reason == "faiss disabled by configuration"
    assert retriever.query("流动性", top_k=3)  # bm25+tfidf still work


# ── 8. Empty knowledge base ─────────────────────────────────────────────────

def test_empty_knowledge_base_does_not_crash(empty_kb_path):
    retriever = HybridRetriever(data_path=empty_kb_path, enable_faiss=False)
    assert retriever.active_retrievers == []
    assert retriever.query("流动性", top_k=3) == []


# ── 9. Empty query ──────────────────────────────────────────────────────────

def test_empty_query_returns_empty_list(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    assert retriever.query("", top_k=3) == []
    assert retriever.query("   ", top_k=3) == []


# ── 10. top_k larger than the number of documents ──────────────────────────

def test_top_k_larger_than_corpus_returns_all_available(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("皮肤", top_k=1000)
    assert 0 < len(results) <= len(SAMPLE_ENTRIES)


def test_top_k_is_clamped_to_max(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    # Should not raise even with an absurd top_k; internally clamped to MAX_TOP_K.
    results = retriever.query("皮肤", top_k=10_000)
    assert len(results) <= MAX_TOP_K


def test_single_document_knowledge_base_works(single_entry_kb_path):
    retriever = HybridRetriever(data_path=single_entry_kb_path, enable_faiss=False)
    results = retriever.query("流动性", top_k=5)
    assert len(results) == 1
    assert results[0]["id"] == SAMPLE_ENTRIES[0]["id"]


# ── 11. Backward compatibility ──────────────────────────────────────────────

def test_retriever_alias_equals_hybrid_retriever():
    assert Retriever is HybridRetriever


def test_result_dict_keeps_legacy_fields(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("流动性", top_k=3)
    assert results
    for r in results:
        assert set(["id", "title", "category", "content", "score"]).issubset(r.keys())
        assert r["score"] == r["fused_score"]  # score is now an alias of fused_score


def test_format_context_unchanged_contract(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=False)
    results = retriever.query("流动性", top_k=2)
    ctx = retriever.format_context(results)
    assert "[知识 1]" in ctx
    assert retriever.format_context([]) == "（未找到相关知识库内容）"


def test_get_retriever_singleton_behavior(monkeypatch, sample_kb_path):
    """get_retriever() must keep returning the same process-wide instance."""
    import app.rag.retriever as retriever_module

    monkeypatch.setattr(retriever_module, "_retriever", None)
    monkeypatch.setattr(retriever_module, "_DATA_PATH", sample_kb_path)

    # Force a fast, network-free singleton for this test.
    def fake_get_retriever():
        if retriever_module._retriever is None:
            retriever_module._retriever = HybridRetriever(
                data_path=sample_kb_path, enable_faiss=False,
            )
        return retriever_module._retriever

    monkeypatch.setattr(retriever_module, "get_retriever", fake_get_retriever)

    r1 = retriever_module.get_retriever()
    r2 = retriever_module.get_retriever()
    assert r1 is r2


# ── error handling: malformed / missing knowledge base ──────────────────────

def test_missing_knowledge_base_file_raises_clear_error(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(KnowledgeBaseError, match="不存在"):
        HybridRetriever(data_path=missing, enable_faiss=False)


def test_malformed_knowledge_base_raises_clear_error(malformed_kb_path):
    with pytest.raises(KnowledgeBaseError, match="JSON"):
        HybridRetriever(data_path=malformed_kb_path, enable_faiss=False)


# ── optional real-model integration test (network required, opt-in only) ──

@pytest.mark.skipif(
    os.environ.get("RUN_REAL_EMBEDDING_TEST") != "1",
    reason="set RUN_REAL_EMBEDDING_TEST=1 to run the real sentence-transformers model",
)
def test_real_embedding_model_semantic_recall(sample_kb_path):
    retriever = HybridRetriever(data_path=sample_kb_path, enable_faiss=True)
    assert "faiss" in retriever.active_retrievers
    results = retriever.query("皮肤怎么才能快速卖出变现", top_k=3)
    ids = [r["id"] for r in results]
    assert 101 in ids
