"""Reproducible retrieval evaluation; no LLM calls or synthetic embeddings.

Run from backend/: python -m app.rag.evaluation --output evaluation/results.json
Use --semantic explicitly to download/use the configured real embedding model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import mean
from time import perf_counter

import numpy as np
from app.rag.retriever import HybridRetriever

BACKEND = Path(__file__).resolve().parents[2]


def ranking_metrics(ranked: list[int], relevant: list[int], k: int) -> dict:
    if k < 1 or not relevant:
        raise ValueError('k and relevance judgments must be nonempty')
    # A duplicate result must not inflate recall or nDCG.
    ranked = list(dict.fromkeys(ranked))[:k]
    gold = set(relevant)
    hits = [i + 1 for i, doc_id in enumerate(ranked) if doc_id in gold]
    dcg = sum(1 / math.log2(rank + 1) for rank in hits)
    ideal = sum(1 / math.log2(rank + 1) for rank in range(1, min(k, len(gold)) + 1))
    return {'hit_rate': float(bool(hits)), 'recall': len(hits) / len(gold),
            'mrr': 1 / hits[0] if hits else 0.0, 'ndcg': dcg / ideal}


def evaluate(retriever, cases: list[dict], k: int = 3) -> dict:
    if not cases:
        raise ValueError('evaluation cases cannot be empty')
    rows = []
    for case in cases:
        started = perf_counter()
        result = retriever.search(case['query'], k)
        ids = [r['id'] for r in result['results']]
        rows.append({**case, 'retrieved_ids': ids,
                     'metrics': ranking_metrics(ids, case['relevant_ids'], k),
                     'latency_ms': round((perf_counter() - started) * 1000, 3),
                     'active_retrievers': result['meta']['active_retrievers']})
    def summarize(group):
        return {'count': len(group), **{m: round(mean(r['metrics'][m] for r in group), 4)
                for m in ['hit_rate', 'recall', 'mrr', 'ndcg']}}
    return {'summary': summarize(rows),
            'by_language': {lang: summarize([r for r in rows if r['language'] == lang])
                            for lang in sorted({r['language'] for r in rows})},
            'latency_ms': {'p50': round(float(np.percentile([r['latency_ms'] for r in rows], 50)), 3),
                           'p95': round(float(np.percentile([r['latency_ms'] for r in rows], 95)), 3)},
            'cases': rows}


def regression_failures(report: dict, baseline: dict) -> list[str]:
    for key in ('dataset_sha256', 'corpus_sha256', 'top_k'):
        if report[key] != baseline[key]:
            raise ValueError(f'{key} changed; review labels/corpus and explicitly regenerate the baseline')
    failures = []
    for mode, old in baseline['modes'].items():
        if mode not in report['modes']:
            failures.append(f'{mode}: missing evaluation')
            continue
        for metric in ('hit_rate', 'recall', 'mrr', 'ndcg'):
            actual = report['modes'][mode]['summary'][metric]
            expected = old['summary'][metric]
            if actual + .0001 < expected:
                failures.append(f'{mode}/{metric}: {actual} < {expected}')
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=BACKEND / 'evaluation/queries.json')
    parser.add_argument('--knowledge', type=Path, default=BACKEND / 'data/knowledge.json')
    parser.add_argument('--output', type=Path, default=BACKEND / 'evaluation/results.json')
    parser.add_argument('--top-k', type=int, choices=range(1, 21), default=3)
    parser.add_argument('--semantic', action='store_true')
    parser.add_argument('--baseline', type=Path, help='Fail on metric regression against a matching corpus/query baseline')
    args = parser.parse_args()
    if args.baseline and args.output.resolve() == args.baseline.resolve():
        parser.error('output must not overwrite the baseline')
    raw = args.dataset.read_bytes()
    dataset = json.loads(raw)
    cases = dataset['queries']
    ids = {e['id'] for e in json.loads(args.knowledge.read_text())}
    if len({c['id'] for c in cases}) != len(cases):
        parser.error('duplicate query IDs')
    if any(not c['relevant_ids'] or set(c['relevant_ids']) - ids for c in cases):
        parser.error('each query needs valid relevance judgments')
    modes = {'tfidf': ('tfidf',), 'bm25': ('bm25',), 'lexical_rrf': ('tfidf', 'bm25')}
    if args.semantic:
        modes['hybrid_rrf'] = ('tfidf', 'bm25', 'faiss')
    report = {'dataset_version': dataset['version'], 'dataset_sha256': hashlib.sha256(raw).hexdigest(),
              'corpus_sha256': hashlib.sha256(args.knowledge.read_bytes()).hexdigest(),
              'top_k': args.top_k, 'corpus_size': len(ids),
              'limitations': dataset['limitations'], 'modes': {}}
    for name, engines in modes.items():
        retriever = HybridRetriever(args.knowledge, engines=engines, enable_faiss=args.semantic)
        if name == 'hybrid_rrf' and 'faiss' not in retriever.active_retrievers:
            parser.error('semantic model unavailable; refusing to label lexical fallback as hybrid results')
        result = evaluate(retriever, cases, args.top_k)
        if name == 'hybrid_rrf' and any('faiss' not in row['active_retrievers'] for row in result['cases']):
            parser.error('semantic retrieval failed during evaluation; no complete hybrid report produced')
        report['modes'][name] = result
        print(name, json.dumps(result['summary']))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.baseline:
        try:
            failures = regression_failures(report, json.loads(args.baseline.read_text()))
        except ValueError as exc:
            parser.error(str(exc))
        if failures:
            parser.exit(1, 'Retrieval regression:\n' + '\n'.join(failures) + '\n')


if __name__ == '__main__':
    main()
