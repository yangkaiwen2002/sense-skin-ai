# Retrieval evaluation

Run from `backend/`:

```bash
python -m app.rag.evaluation --output evaluation/ci-results.json --baseline evaluation/results.json
# Optional: actual semantic model, may download weights; never silently falls back.
python -m app.rag.evaluation --semantic --output evaluation/semantic-results.json
```

`queries.json` contains **24 author-labeled smoke queries: 12 Chinese and 12 English**, over the existing 32-entry corpus. It covers wear, StatTrak, rental decisions, deposits, tournaments, individual items, platform differences, updates, liquidity, and sticker scraping. It is **not a held-out benchmark**, exhaustive relevance labeling, or a fact check of source content. English queries deliberately expose cross-language limitations of lexical retrieval. Do not advertise these numbers as overall product accuracy.

Initial reproducible baseline (`top_k=3`; actual lexical engines, no LLM, no fake embeddings):

| Mode | Hit@3 | Recall@3 | MRR@3 | nDCG@3 |
| --- | ---: | ---: | ---: | ---: |
| TF-IDF | 0.9167 | 0.8125 | 0.8125 | 0.7629 |
| BM25 | 0.8333 | 0.7292 | 0.7361 | 0.6829 |
| Lexical RRF | 0.9167 | 0.7917 | 0.8125 | 0.7468 |

**Fusion does not improve every metric.** TF-IDF alone retrieves more of the labeled relevant entries at three in this small set. No weights were tuned to these queries. The report keeps every query, gold IDs, returned IDs, active engines, and language breakdown to make this visible.

- Hit@k: whether at least one labeled relevant document appears.
- Recall@k: fraction of all labeled relevant documents retrieved.
- MRR@k: reciprocal rank of the first relevant document, or zero.
- nDCG@k: binary relevance, log-discounted gain normalized by the ideal ranking.
- All aggregates include misses. Duplicate IDs cannot inflate metrics.
- Latency excludes initialization/model loading and is machine dependent; it is informational and not gated.
- Corpus and dataset SHA-256 hashes plus k must match before baseline comparison. CI fails if a recorded ranking metric drops. Changing corpus/labels requires explicit baseline review.
- `--semantic` refuses to report hybrid results if FAISS initialization or any semantic query fails. The default report evaluates the lexical fallback only.

Next useful evaluation: independently label more paraphrases and out-of-domain questions; test the real multilingual model; use a separate tuning split; measure answer citation accuracy independently of retrieval ranking.
