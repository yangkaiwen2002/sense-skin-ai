"""Unit tests for app/rag/fusion.py — Reciprocal Rank Fusion correctness."""
from __future__ import annotations

import pytest

from app.rag.fusion import FusionWeights, reciprocal_rank_fusion


def test_rrf_matches_hand_computed_formula():
    """RRF_score(d) = sum( weight_i / (k + rank_i) ) for each retriever that found d."""
    ranked_lists = {
        "faiss": [(1, 0.9), (2, 0.5)],
        "bm25":  [(2, 5.0), (1, 3.0)],
        "tfidf": [(1, 0.4)],
    }
    weights = {"faiss": 0.45, "bm25": 0.35, "tfidf": 0.20}
    k = 60

    hits = reciprocal_rank_fusion(ranked_lists, weights, k=k)
    scores = {h.doc_id: h.fused_score for h in hits}

    # doc 1: faiss rank 1, bm25 rank 2, tfidf rank 1
    expected_1 = 0.45 / (k + 1) + 0.35 / (k + 2) + 0.20 / (k + 1)
    # doc 2: faiss rank 2, bm25 rank 1
    expected_2 = 0.45 / (k + 2) + 0.35 / (k + 1)

    assert scores[1] == pytest.approx(expected_1, rel=1e-9)
    assert scores[2] == pytest.approx(expected_2, rel=1e-9)


def test_rrf_weights_renormalize_when_a_retriever_is_missing():
    """If FAISS didn't run, bm25+tfidf weights should renormalize to sum to 1,
    not just use their raw 0.35/0.20 (which would shrink every fused score)."""
    ranked_lists = {"bm25": [(1, 5.0)], "tfidf": [(1, 0.4)]}
    weights = FusionWeights.as_dict()  # faiss=0.45, bm25=0.35, tfidf=0.20

    hits = reciprocal_rank_fusion(ranked_lists, weights, k=60)
    assert len(hits) == 1

    renorm_bm25 = 0.35 / (0.35 + 0.20)
    renorm_tfidf = 0.20 / (0.35 + 0.20)
    expected = renorm_bm25 / 61 + renorm_tfidf / 61
    assert hits[0].fused_score == pytest.approx(expected, rel=1e-9)


def test_rrf_dedups_document_found_by_multiple_retrievers():
    """A doc found by all three retrievers must appear exactly once in the output,
    with its score being the sum of all three contributions."""
    ranked_lists = {
        "faiss": [(7, 0.99)],
        "bm25":  [(7, 10.0)],
        "tfidf": [(7, 0.5)],
    }
    weights = FusionWeights.as_dict()
    hits = reciprocal_rank_fusion(ranked_lists, weights, k=60)

    assert len(hits) == 1
    assert hits[0].doc_id == 7
    assert set(hits[0].per_retriever.keys()) == {"faiss", "bm25", "tfidf"}


def test_rrf_sorts_by_fused_score_descending():
    ranked_lists = {"bm25": [(5, 3.0), (3, 2.0), (9, 1.0)]}
    hits = reciprocal_rank_fusion(ranked_lists, {"bm25": 1.0}, k=60)
    scores = [h.fused_score for h in hits]
    assert scores == sorted(scores, reverse=True)
    assert [h.doc_id for h in hits] == [5, 3, 9]  # rank order preserved for a single retriever


def test_rrf_breaks_ties_by_ascending_doc_id():
    # Two independent retrievers each place a different doc at rank 1 with an
    # identical weight -> a genuine fused_score tie between doc 1 and doc 2.
    tie_lists = {
        "bm25":  [(2, 9.0)],
        "tfidf": [(1, 9.0)],
    }
    hits = reciprocal_rank_fusion(tie_lists, {"bm25": 0.5, "tfidf": 0.5}, k=60)
    assert hits[0].fused_score == pytest.approx(hits[1].fused_score, rel=1e-9)
    assert [h.doc_id for h in hits] == [1, 2]  # tie broken by ascending doc_id


def test_rrf_empty_ranked_lists_returns_empty():
    assert reciprocal_rank_fusion({}, FusionWeights.as_dict(), k=60) == []
