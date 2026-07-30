"""
Reciprocal Rank Fusion (RRF) for combining ranked result lists from
independent retrievers (FAISS / BM25 / TF-IDF) whose raw scores live on
incomparable scales (cosine similarity vs BM25's unbounded term-weight sum
vs TF-IDF cosine similarity) — summing raw scores directly would let
whichever retriever happens to produce the largest numbers dominate.

    RRF_score(d) = sum_over_retrievers( weight / (k + rank) )

`rank` is 1-indexed. A document not returned by a given retriever's
candidate list simply contributes no term from that retriever — it is not
penalized beyond that.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

DEFAULT_RRF_K = 60


class FusionWeights:
    """Default per-retriever weights, centralised so they're easy to tune."""
    FAISS = 0.45
    BM25  = 0.35
    TFIDF = 0.20

    @classmethod
    def as_dict(cls) -> dict[str, float]:
        return {"faiss": cls.FAISS, "bm25": cls.BM25, "tfidf": cls.TFIDF}


@dataclass
class FusedHit:
    doc_id: int
    fused_score: float
    # per_retriever["faiss"] = {"rank": 1, "score": 0.83}
    per_retriever: dict[str, dict[str, float]] = field(default_factory=dict)


def reciprocal_rank_fusion(
    ranked_lists: Mapping[str, Sequence[tuple[int, float]]],
    weights: Mapping[str, float],
    k: int = DEFAULT_RRF_K,
) -> list[FusedHit]:
    """
    ranked_lists: {retriever_name: [(doc_id, raw_score), ...]}, each list
                  already sorted best-first by that retriever's own metric.
    weights:      {retriever_name: weight}. Only retrievers present in
                  `ranked_lists` contribute; their weights are renormalized
                  to sum to 1 so a retriever that's simply unavailable
                  (e.g. FAISS failed to load) doesn't shrink the total
                  fused score for every document — the remaining retrievers'
                  relative influence is preserved automatically.

    Returns fused hits sorted by fused_score descending; ties are broken by
    ascending doc_id for a fully deterministic, stable ordering.
    """
    active = [name for name in ranked_lists if name in weights]
    total_w = sum(weights[name] for name in active)

    if total_w > 0:
        norm_weights = {name: weights[name] / total_w for name in active}
    elif active:
        # all listed weights were zero/negative — fall back to equal weighting
        norm_weights = {name: 1.0 / len(active) for name in active}
    else:
        norm_weights = {}

    scores: dict[int, float] = {}
    details: dict[int, dict[str, dict[str, float]]] = {}

    for name in active:
        w = norm_weights[name]
        for rank, (doc_id, raw_score) in enumerate(ranked_lists[name], start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + w / (k + rank)
            details.setdefault(doc_id, {})[name] = {"rank": rank, "score": float(raw_score)}

    hits = [
        FusedHit(doc_id=doc_id, fused_score=score, per_retriever=details.get(doc_id, {}))
        for doc_id, score in scores.items()
    ]
    # Stable, deterministic tie-break: fused_score desc, then doc_id asc.
    hits.sort(key=lambda h: (-h.fused_score, h.doc_id))
    return hits
